# sangram_tutor/ml/recommendation.py
import json
import logging
import math
import random
import faiss
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy.orm import Session

from sangram_tutor.models.curriculum import CurriculumContent, CurriculumTopic
from sangram_tutor.models.progress import Progress
from sangram_tutor.models.user import User

logger = logging.getLogger(__name__)

# Directory where vector indices are stored
VECTOR_DIR = Path("./vector_indices")


class ContentRecommender:
    """
    Recommends personalized content based on user history, preferences,
    and collaborative filtering.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.index = None
        self.id_mapping = None
        self._load_vector_index()
    
    def _load_vector_index(self) -> None:
        """Load the vector index if it exists."""
        index_path = VECTOR_DIR / "content_embeddings.index"
        mapping_path = VECTOR_DIR / "content_id_mapping.json"
        
        if index_path.exists() and mapping_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                with open(mapping_path, 'r') as f:
                    self.id_mapping = json.load(f)
                logger.info("Successfully loaded vector index and mapping")
            except Exception as e:
                logger.error(f"Error loading vector index: {e}")
                self.index = None
                self.id_mapping = None
        else:
            logger.warning("Vector index or mapping file not found")
    
    def get_similar_content(self, content_id: int, limit: int = 5) -> List[Dict]:
        """
        Find content similar to the given content ID.
        
        Args:
            content_id: ID of the content to find similar items for
            limit: Maximum number of similar items to return
            
        Returns:
            List of similar content items with similarity scores
        """
        if not self.index or not self.id_mapping:
            logger.warning("Vector index not loaded, can't find similar content")
            return self._fallback_recommendations(content_id, limit)
        
        # Find content in database
        content = self.db.query(CurriculumContent).filter_by(id=content_id).first()
        if not content:
            logger.error(f"Content with ID {content_id} not found")
            return []
        
        # Find content index in vector database
        content_idx = None
        for idx, c_id in self.id_mapping.items():
            if int(c_id) == content_id:
                content_idx = int(idx)
                break
        
        if content_idx is None:
            logger.warning(f"Content ID {content_id} not found in vector index")
            return self._fallback_recommendations(content_id, limit)
        
        # Get the embedding for this content
        embedding = np.zeros((1, self.index.d), dtype=np.float32)
        faiss.reconstruct(self.index, content_idx, embedding[0])
        
        # Search for similar content
        k = min(limit + 1, self.index.ntotal)  # +1 to account for self-match
        distances, indices = self.index.search(embedding, k)
        
        # Format results (excluding the query content itself)
        results = []
        for i, idx in enumerate(indices[0]):
            # Skip self-match
            if int(idx) == content_idx:
                continue
                
            # Get the content ID from the mapping
            similar_content_id = int(self.id_mapping.get(str(int(idx)), -1))
            if similar_content_id == -1:
                continue
                
            # Get content from database
            similar_content = self.db.query(CurriculumContent).filter_by(id=similar_content_id).first()
            if not similar_content:
                continue
                
            # Calculate similarity score (convert distance to similarity)
            similarity = max(0, 100 - distances[0][i] * 10)  # Scale to 0-100
            
            results.append({
                "id": similar_content.id,
                "title": similar_content.title,
                "similarity_score": round(float(similarity), 2),
                "content_type": similar_content.content_type.value,
                "difficulty_level": similar_content.difficulty_level.value
            })
            
            if len(results) >= limit:
                break
                
        return results
    
    def _fallback_recommendations(self, content_id: int, limit: int = 5) -> List[Dict]:
        """
        Fallback recommendation method when vector search is unavailable.
        Uses simple metadata-based filtering.
        
        Args:
            content_id: ID of the content to find similar items for
            limit: Maximum number of similar items to return
            
        Returns:
            List of similar content items with similarity scores
        """
        # Find content in database
        content = self.db.query(CurriculumContent).filter_by(id=content_id).first()
        if not content:
            logger.error(f"Content with ID {content_id} not found")
            return []
        
        # Find other content in the same topic with similar difficulty
        similar_content = self.db.query(CurriculumContent).filter(
            CurriculumContent.topic_id == content.topic_id,
            CurriculumContent.id != content_id
        ).limit(limit * 2).all()
        
        if not similar_content:
            return []
        
        # Score similarity based on metadata
        results = []
        for item in similar_content:
            # Base similarity score
            similarity = 70.0  # Start with 70% similarity for same topic
            
            # Adjust based on difficulty difference
            if item.difficulty_level == content.difficulty_level:
                similarity += 20.0
            elif abs(ord(item.difficulty_level.value[0]) - ord(content.difficulty_level.value[0])) == 1:
                similarity += 10.0  # Adjacent difficulty levels
            
            # Adjust based on content type
            if item.content_type == content.content_type:
                similarity += 10.0
            
            results.append({
                "id": item.id,
                "title": item.title,
                "similarity_score": round(similarity, 2),
                "content_type": item.content_type.value,
                "difficulty_level": item.difficulty_level.value
            })
        
        # Sort by similarity (highest first) and limit results
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]
    
    def get_personalized_recommendations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """
        Generate personalized content recommendations for a user.
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended content items with relevance scores
        """
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return []
        
        # Get user's progress data
        progress = self.db.query(Progress).filter_by(user_id=user_id).all()
        
        # If user has no progress, recommend beginner content for their grade
        if not progress:
            return self._recommend_for_new_user(user, limit)
        
        # Get recently completed content
        completed_progress = [p for p in progress if p.status == "completed" and p.score is not None]
        if not completed_progress:
            return self._recommend_for_new_user(user, limit)
        
        # Sort by last interaction (most recent first)
        completed_progress.sort(key=lambda p: p.last_interaction or 0, reverse=True)
        
        # Use the most recently completed content with high score as seed
        high_score_progress = [p for p in completed_progress[:5] if p.score and p.score >= 80]
        
        if high_score_progress:
            seed_content_id = high_score_progress[0].content_id
        else:
            seed_content_id = completed_progress[0].content_id
        
        # Get similar content to the seed
        similar_content = self.get_similar_content(seed_content_id, limit=limit*2)
        
        # Filter out already completed content
        completed_ids = {p.content_id for p in progress}
        recommendations = [
            item for item in similar_content if item["id"] not in completed_ids
        ]
        
        # If we don't have enough recommendations, add some from topic-based recommendations
        if len(recommendations) < limit:
            topic_recs = self._get_topic_based_recommendations(user, progress, limit*2)
            for rec in topic_recs:
                if rec["id"] not in completed_ids and not any(r["id"] == rec["id"] for r in recommendations):
                    recommendations.append(rec)
                    if len(recommendations) >= limit:
                        break
        
        return recommendations[:limit]
    
    def _recommend_for_new_user(self, user: User, limit: int = 5) -> List[Dict]:
        """Generate recommendations for a new user with no history."""
        # Find beginner content appropriate for the user's grade level
        if user.grade_level:
            # Get topics for the user's grade
            topics = self.db.query(CurriculumTopic).filter_by(grade_level=user.grade_level).all()
            topic_ids = [topic.id for topic in topics]
            
            # Get beginner content for these topics
            beginner_content = self.db.query(CurriculumContent).filter(
                CurriculumContent.topic_id.in_(topic_ids),
                CurriculumContent.difficulty_level == "beginner"
            ).limit(limit).all()
            
            if beginner_content:
                return [
                    {
                        "id": content.id,
                        "title": content.title,
                        "relevance_score": 90.0,  # High relevance for grade-appropriate content
                        "content_type": content.content_type.value,
                        "difficulty_level": content.difficulty_level.value,
                        "recommendation_reason": "Grade-appropriate introduction"
                    }
                    for content in beginner_content
                ]
        
        # Fallback: recommend any beginner content
        beginner_content = self.db.query(CurriculumContent).filter_by(
            difficulty_level="beginner"
        ).limit(limit).all()
        
        return [
            {
                "id": content.id,
                "title": content.title,
                "relevance_score": 80.0,
                "content_type": content.content_type.value,
                "difficulty_level": content.difficulty_level.value,
                "recommendation_reason": "Beginner-friendly content"
            }
            for content in beginner_content
        ]
    
    def _get_topic_based_recommendations(
        self, user: User, progress: List[Progress], limit: int = 5
    ) -> List[Dict]:
        """Generate recommendations based on topics the user has engaged with."""
        # Count interaction with each topic
        topic_interactions = {}
        
        for p in progress:
            if not p.content:
                continue
                
            topic_id = p.content.topic_id
            if topic_id not in topic_interactions:
                topic_interactions[topic_id] = {
                    "count": 0,
                    "score_sum": 0,
                    "score_count": 0
                }
            
            topic_interactions[topic_id]["count"] += 1
            
            if p.score is not None:
                topic_interactions[topic_id]["score_sum"] += p.score
                topic_interactions[topic_id]["score_count"] += 1
        
        # Calculate average score for each topic
        for topic_id, data in topic_interactions.items():
            if data["score_count"] > 0:
                data["avg_score"] = data["score_sum"] / data["score_count"]
            else:
                data["avg_score"] = None
        
        # Find content from most engaged topics that hasn't been completed
        completed_ids = {p.content_id for p in progress}
        recommendations = []
        
        # Sort topics by engagement (most engaged first)
        sorted_topics = sorted(
            topic_interactions.items(), 
            key=lambda x: x[1]["count"], 
            reverse=True
        )
        
        for topic_id, data in sorted_topics:
            # Determine appropriate difficulty based on average score
            if data["avg_score"] is None or data["avg_score"] < 60:
                difficulty = "beginner"
            elif data["avg_score"] < 75:
                difficulty = "easy"
            elif data["avg_score"] < 90:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
            # Find content of appropriate difficulty
            topic_content = self.db.query(CurriculumContent).filter(
                CurriculumContent.topic_id == topic_id,
                CurriculumContent.id.notin_(completed_ids),
                CurriculumContent.difficulty_level == difficulty
            ).all()
            
            for content in topic_content:
                relevance = 75.0 + (data["count"] / max(topic_interactions.values(), key=lambda x: x["count"])["count"]) * 15.0
                
                recommendations.append({
                    "id": content.id,
                    "title": content.title,
                    "relevance_score": round(relevance, 2),
                    "content_type": content.content_type.value,
                    "difficulty_level": content.difficulty_level.value,
                    "recommendation_reason": "Based on your interests"
                })
                
                if len(recommendations) >= limit:
                    break
            
            if len(recommendations) >= limit:
                break
        
        return recommendations


# sangram_tutor/ml/learning_style_detector.py
import logging
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from sangram_tutor.models.progress import Progress
from sangram_tutor.models.user import User, LearningStyle

logger = logging.getLogger(__name__)

class LearningStyleDetector:
    """
    Detects and predicts user learning styles based on interaction patterns.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def predict_learning_styles(self, user_id: int) -> Dict[str, float]:
        """
        Predict learning style affinities for a user.
        
        Args:
            user_id: ID of the user to predict learning styles for
            
        Returns:
            Dictionary mapping learning style to affinity score (0-1)
        """
        # Get user information
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return {}
        
        # Get user's progress data
        progress_records = self.db.query(Progress).filter_by(user_id=user_id).all()
        
        if not progress_records:
            # Not enough data - return balanced affinities
            return {style.value: 0.5 for style in LearningStyle}
        
        # Initialize learning style affinities
        style_affinities = {style.value: 0.5 for style in LearningStyle}
        
        # Analyze performance by content type
        content_type_performance = self._analyze_content_type_performance(progress_records)
        
        # Update affinities based on performance patterns
        if content_type_performance:
            self._update_affinities_from_performance(style_affinities, content_type_performance)
        
        # Analyze engagement patterns
        engagement_patterns = self._analyze_engagement_patterns(progress_records)
        
        # Update affinities based on engagement patterns
        if engagement_patterns:
            self._update_affinities_from_engagement(style_affinities, engagement_patterns)
        
        # Normalize affinities to ensure they sum to a consistent value
        total = sum(style_affinities.values())
        if total > 0:
            for style in style_affinities:
                style_affinities[style] = round(style_affinities[style] / total * len(style_affinities), 2)
        
        return style_affinities
    
    def _analyze_content_type_performance(self, progress_records: List[Progress]) -> Dict:
        """Analyze user performance by content type."""
        type_performance = {}
        
        for progress in progress_records:
            if not progress.content or progress.score is None:
                continue
                
            content_type = progress.content.content_type.value
            if content_type not in type_performance:
                type_performance[content_type] = {
                    "scores": [],
                    "time_spent": [],
                    "attempts": []
                }
            
            type_performance[content_type]["scores"].append(progress.score)
            
            if progress.time_spent_seconds:
                type_performance[content_type]["time_spent"].append(progress.time_spent_seconds)
                
            if progress.attempts:
                type_performance[content_type]["attempts"].append(progress.attempts)
        
        # Calculate averages
        result = {}
        for content_type, data in type_performance.items():
            result[content_type] = {
                "avg_score": sum(data["scores"]) / len(data["scores"]) if data["scores"] else None,
                "avg_time": sum(data["time_spent"]) / len(data["time_spent"]) if data["time_spent"] else None,
                "avg_attempts": sum(data["attempts"]) / len(data["attempts"]) if data["attempts"] else None,
                "count": len(data["scores"])
            }
        
        return result
    
    def _analyze_engagement_patterns(self, progress_records: List[Progress]) -> Dict:
        """Analyze engagement patterns across different content types."""
        type_engagement = {}
        
        for progress in progress_records:
            if not progress.content or not progress.engagement_score:
                continue
                
            content_type = progress.content.content_type.value
            if content_type not in type_engagement:
                type_engagement[content_type] = []
                
            type_engagement[content_type].append(progress.engagement_score)
        
        # Calculate average engagement by content type
        result = {}
        for content_type, scores in type_engagement.items():
            if scores:
                result[content_type] = sum(scores) / len(scores)
        
        return result
    
    def _update_affinities_from_performance(
        self, affinities: Dict[str, float], performance: Dict
    ) -> None:
        """Update learning style affinities based on performance data."""
        # Mapping of content types to learning styles they indicate
        content_type_mapping = {
            "concept": [LearningStyle.READING_WRITING, LearningStyle.LOGICAL],
            "example": [LearningStyle.VISUAL, LearningStyle.LOGICAL],
            "exercise": [LearningStyle.KINESTHETIC, LearningStyle.READING_WRITING],
            "game": [LearningStyle.KINESTHETIC, LearningStyle.VISUAL, LearningStyle.SOCIAL],
            "quiz": [LearningStyle.LOGICAL, LearningStyle.SOLITARY],
            "assessment": [LearningStyle.LOGICAL, LearningStyle.SOLITARY]
        }
        
        # Find best and worst performing content types
        if not performance:
            return
            
        sorted_by_score = sorted(
            [(ctype, data["avg_score"]) for ctype, data in performance.items() if data["avg_score"] is not None],
            key=lambda x: x[1],
            reverse=True
        )
        
        if not sorted_by_score:
            return
            
        # Boost affinities for learning styles associated with high-performing content types
        for content_type, score in sorted_by_score[:2]:  # Top 2 performing types
            if score < 70:  # Only consider good performance
                continue
                
            for style in content_type_mapping.get(content_type, []):
                affinities[style.value] += 0.2
        
        # Reduce affinities for learning styles associated with low-performing content types
        for content_type, score in sorted_by_score[-2:]:  # Bottom 2 performing types
            if score > 60:  # Only consider poor performance
                continue
                
            for style in content_type_mapping.get(content_type, []):
                affinities[style.value] = max(0.1, affinities[style.value] - 0.1)
    
    def _update_affinities_from_engagement(
        self, affinities: Dict[str, float], engagement: Dict
    ) -> None:
        """Update learning style affinities based on engagement data."""
        # Mapping of content types to learning styles they indicate
        content_type_mapping = {
            "concept": [LearningStyle.AUDITORY, LearningStyle.READING_WRITING],
            "example": [LearningStyle.VISUAL, LearningStyle.AUDITORY],
            "exercise": [LearningStyle.KINESTHETIC, LearningStyle.LOGICAL],
            "game": [LearningStyle.KINESTHETIC, LearningStyle.SOCIAL],
            "quiz": [LearningStyle.READING_WRITING, LearningStyle.SOLITARY],
            "assessment": [LearningStyle.LOGICAL, LearningStyle.SOLITARY]
        }
        
        # Find highest engagement content types
        sorted_by_engagement = sorted(
            engagement.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if not sorted_by_engagement:
            return
            
        # Boost affinities for learning styles associated with high-engagement content types
        for content_type, engagement_score in sorted_by_engagement[:2]:  # Top 2 engaging types
            if engagement_score < 0.6:  # Only consider good engagement
                continue
                
            for style in content_type_mapping.get(content_type, []):
                affinities[style.value] += 0.15
        
        # Slightly reduce affinities for learning styles associated with low-engagement content types
        for content_type, engagement_score in sorted_by_engagement[-2:]:  # Bottom 2 engaging types
            if engagement_score > 0.4:  # Only consider poor engagement
                continue
                
            for style in content_type_mapping.get(content_type, []):
                affinities[style.value] = max(0.1, affinities[style.value] - 0.05)
