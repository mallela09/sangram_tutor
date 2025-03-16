# sangram_tutor/ml/learning_path.py
import json
import logging
import math
import random
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from sqlalchemy.orm import Session

from sangram_tutor.models.curriculum import (
    CurriculumContent, ContentType, DifficultyLevel
)
from sangram_tutor.models.progress import Progress, CompletionStatus
from sangram_tutor.models.user import User, LearningStyle

logger = logging.getLogger(__name__)

# Difficulty level progression mapping
DIFFICULTY_PROGRESSION = {
    DifficultyLevel.BEGINNER: DifficultyLevel.EASY,
    DifficultyLevel.EASY: DifficultyLevel.MEDIUM,
    DifficultyLevel.MEDIUM: DifficultyLevel.HARD,
    DifficultyLevel.HARD: DifficultyLevel.EXPERT,
    DifficultyLevel.EXPERT: DifficultyLevel.EXPERT,
}

# Content type weights based on learning style
# These weights determine how much different content types are recommended
# based on the user's learning style
LEARNING_STYLE_WEIGHTS = {
    LearningStyle.VISUAL: {
        ContentType.CONCEPT: 0.8,
        ContentType.EXAMPLE: 1.0,
        ContentType.EXERCISE: 0.6,
        ContentType.GAME: 1.0,
        ContentType.QUIZ: 0.7,
        ContentType.ASSESSMENT: 0.5,
    },
    LearningStyle.AUDITORY: {
        ContentType.CONCEPT: 1.0,
        ContentType.EXAMPLE: 0.8,
        ContentType.EXERCISE: 0.6,
        ContentType.GAME: 0.7,
        ContentType.QUIZ: 0.7,
        ContentType.ASSESSMENT: 0.6,
    },
    LearningStyle.READING_WRITING: {
        ContentType.CONCEPT: 0.9,
        ContentType.EXAMPLE: 0.8,
        ContentType.EXERCISE: 1.0,
        ContentType.GAME: 0.6,
        ContentType.QUIZ: 0.9,
        ContentType.ASSESSMENT: 0.8,
    },
    LearningStyle.KINESTHETIC: {
        ContentType.CONCEPT: 0.6,
        ContentType.EXAMPLE: 0.7,
        ContentType.EXERCISE: 0.9,
        ContentType.GAME: 1.0,
        ContentType.QUIZ: 0.8,
        ContentType.ASSESSMENT: 0.7,
    },
    LearningStyle.LOGICAL: {
        ContentType.CONCEPT: 0.9,
        ContentType.EXAMPLE: 0.7,
        ContentType.EXERCISE: 1.0,
        ContentType.GAME: 0.6,
        ContentType.QUIZ: 0.8,
        ContentType.ASSESSMENT: 0.9,
    },
    LearningStyle.SOCIAL: {
        ContentType.CONCEPT: 0.7,
        ContentType.EXAMPLE: 0.8,
        ContentType.EXERCISE: 0.7,
        ContentType.GAME: 1.0,
        ContentType.QUIZ: 0.8,
        ContentType.ASSESSMENT: 0.6,
    },
    LearningStyle.SOLITARY: {
        ContentType.CONCEPT: 0.9,
        ContentType.EXAMPLE: 0.8,
        ContentType.EXERCISE: 0.9,
        ContentType.GAME: 0.5,
        ContentType.QUIZ: 0.8,
        ContentType.ASSESSMENT: 1.0,
    },
}

class LearningPathGenerator:
    """
    Generates personalized learning paths for students based on their
    progress, learning style, and curriculum requirements.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_next_content(self, user_id: int, topic_id: Optional[int] = None) -> Optional[Dict]:
        """
        Recommends the next piece of content for a user based on their
        learning profile and progress.
        
        Args:
            user_id: The ID of the user to generate recommendations for
            topic_id: Optional topic ID to filter content by
            
        Returns:
            Dictionary with content ID and metadata, or None if no suitable content found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return None
        
        # Get user's progress data
        progress_records = self.db.query(Progress).filter(Progress.user_id == user_id).all()
        completed_content_ids = [
            p.content_id for p in progress_records 
            if p.status in (CompletionStatus.COMPLETED, CompletionStatus.MASTERED)
        ]
        
        in_progress_content_ids = [
            p.content_id for p in progress_records 
            if p.status == CompletionStatus.IN_PROGRESS
        ]
        
        # Try to find in-progress content first
        if in_progress_content_ids:
            content = self.db.query(CurriculumContent).filter(
                CurriculumContent.id.in_(in_progress_content_ids)
            ).first()
            if content:
                return self._format_content_response(content)
        
        # Query for available content
        query = self.db.query(CurriculumContent)
        
        # Filter by topic if specified
        if topic_id:
            query = query.filter(CurriculumContent.topic_id == topic_id)
        
        # Filter by grade level
        if user.grade_level:
            # Get topics for the user's grade level
            grade_topics = self.db.query(CurriculumTopic.id).filter(
                CurriculumTopic.grade_level == user.grade_level
            ).all()
            grade_topic_ids = [topic.id for topic in grade_topics]
            query = query.filter(CurriculumContent.topic_id.in_(grade_topic_ids))
        
        # Exclude completed content
        if completed_content_ids:
            query = query.filter(~CurriculumContent.id.in_(completed_content_ids))
        
        # Get all potential content
        candidate_contents = query.all()
        if not candidate_contents:
            logger.info(f"No suitable content found for user {user_id}")
            return None
        
        # Score and rank content based on user's learning profile
        scored_content = self._score_content_for_user(user, candidate_contents, progress_records)
        
        # Return the highest-scoring content
        if not scored_content:
            return None
        
        best_content = scored_content[0]
        return self._format_content_response(best_content[0])
    
    def _score_content_for_user(
        self, 
        user: User, 
        contents: List[CurriculumContent],
        progress_records: List[Progress]
    ) -> List[Tuple[CurriculumContent, float]]:
        """
        Score content items based on the user's learning profile.
        
        Args:
            user: The user to score content for
            contents: List of candidate content items
            progress_records: User's progress records
            
        Returns:
            List of (content, score) tuples, sorted by descending score
        """
        # Extract user learning styles
        learning_styles = [style.name for style in user.learning_styles]
        
        # Default to a balanced profile if no styles are set
        if not learning_styles:
            learning_styles = [LearningStyle.VISUAL, LearningStyle.KINESTHETIC]
        
        # Build progress lookup for quick access
        progress_lookup = {p.content_id: p for p in progress_records}
        
        scored_items = []
        for content in contents:
            # Skip content that has prerequisites not yet completed
            if self._check_missing_prerequisites(content, progress_records):
                continue
            
            base_score = 1.0
            
            # Factor 1: Content type suitability for learning style
            style_score = 0
            for style in learning_styles:
                style_weights = LEARNING_STYLE_WEIGHTS.get(style, {})
                style_score += style_weights.get(content.content_type, 0.7)
            style_score /= len(learning_styles)
            
            # Factor 2: Appropriate difficulty level
            difficulty_score = self._calculate_difficulty_score(user, content, progress_lookup)
            
            # Factor 3: Topic relevance (if we were tracking topic interests)
            topic_score = 1.0  # Placeholder for future enhancement
            
            # Factor 4: Add small random factor to prevent identical recommendations
            randomness = random.uniform(0.95, 1.05)
            
            # Calculate final score (weighted average)
            final_score = (
                style_score * 0.4 +
                difficulty_score * 0.4 +
                topic_score * 0.1
            ) * randomness
            
            scored_items.append((content, final_score))
        
        # Sort by score (descending)
        return sorted(scored_items, key=lambda x: x[1], reverse=True)
    
    def _calculate_difficulty_score(
        self, 
        user: User, 
        content: CurriculumContent,
        progress_lookup: Dict[int, Progress]
    ) -> float:
        """
        Calculate how appropriate the content difficulty is for the user.
        
        Args:
            user: The user to calculate for
            content: The content item
            progress_lookup: Dictionary mapping content IDs to progress records
            
        Returns:
            Difficulty appropriateness score (0-1)
        """
        # Get user's average performance
        topic_progress = [
            p for p in progress_lookup.values() 
            if p.content and p.content.topic_id == content.topic_id
        ]
        
        if not topic_progress:
            # No data for this topic, give middle difficulty content higher scores
            if content.difficulty_level in (DifficultyLevel.EASY, DifficultyLevel.MEDIUM):
                return 0.9
            return 0.7
        
        # Calculate average score on this topic
        scores = [p.score for p in topic_progress if p.score is not None]
        if not scores:
            return 0.8  # No scores yet, slight preference for easier content
        
        avg_score = sum(scores) / len(scores)
        
        # Higher scores mean the user is ready for more difficult content
        if avg_score > 90:  # Excellent performance
            if content.difficulty_level in (DifficultyLevel.HARD, DifficultyLevel.EXPERT):
                return 1.0
            return 0.6
        elif avg_score > 75:  # Good performance
            if content.difficulty_level == DifficultyLevel.MEDIUM:
                return 1.0
            elif content.difficulty_level == DifficultyLevel.HARD:
                return 0.8
            return 0.5
        elif avg_score > 60:  # Average performance
            if content.difficulty_level in (DifficultyLevel.EASY, DifficultyLevel.MEDIUM):
                return 0.9
            return 0.4
        else:  # Struggling
            if content.difficulty_level == DifficultyLevel.BEGINNER:
                return 1.0
            elif content.difficulty_level == DifficultyLevel.EASY:
                return 0.8
            return 0.3
    
    def _check_missing_prerequisites(
        self, 
        content: CurriculumContent, 
        progress_records: List[Progress]
    ) -> bool:
        """
        Check if the content has prerequisites that haven't been completed.
        
        Args:
            content: The content to check
            progress_records: List of user's progress records
            
        Returns:
            True if there are missing prerequisites, False otherwise
        """
        if not content.prerequisites:
            return False
        
        completed_content_ids = {
            p.content_id for p in progress_records 
            if p.status in (CompletionStatus.COMPLETED, CompletionStatus.MASTERED)
        }
        
        for prereq in content.prerequisites:
            if prereq.id not in completed_content_ids:
                return True
        
        return False
    
    def _format_content_response(self, content: CurriculumContent) -> Dict:
        """Format content as a response dictionary."""
        return {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "content_type": content.content_type.value,
            "difficulty_level": content.difficulty_level.value,
            "estimated_time_minutes": content.estimated_time_minutes,
            "content_data": json.loads(content.content_data),
            "topic_id": content.topic_id,
        }


# sangram_tutor/ml/performance_analyzer.py
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from sangram_tutor.models.curriculum import CurriculumContent, ContentType
from sangram_tutor.models.progress import Progress, CompletionStatus
from sangram_tutor.models.user import User

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Analyzes student performance to provide insights and recommendations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_user_performance(self, user_id: int) -> Dict:
        """
        Generate a comprehensive analysis of a user's performance.
        
        Args:
            user_id: ID of the user to analyze
            
        Returns:
            Dictionary with performance metrics and insights
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return {"error": "User not found"}
        
        # Get progress records
        progress_records = self.db.query(Progress).filter(Progress.user_id == user_id).all()
        
        if not progress_records:
            return {
                "message": "Not enough data for analysis",
                "recommendations": [
                    "Complete some activities to generate performance insights"
                ]
            }
        
        # Calculate performance metrics
        overall_score = self._calculate_overall_score(progress_records)
        topic_performance = self._calculate_topic_performance(progress_records)
        strengths_weaknesses = self._identify_strengths_weaknesses(progress_records)
        learning_patterns = self._analyze_learning_patterns(progress_records)
        engagement_metrics = self._calculate_engagement_metrics(progress_records)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            user, 
            progress_records, 
            strengths_weaknesses, 
            engagement_metrics
        )
        
        return {
            "overall_score": overall_score,
            "topic_performance": topic_performance,
            "strengths_weaknesses": strengths_weaknesses,
            "learning_patterns": learning_patterns,
            "engagement_metrics": engagement_metrics,
            "recommendations": recommendations
        }
    
    def _calculate_overall_score(self, progress_records: List[Progress]) -> Dict:
        """Calculate overall performance score and related metrics."""
        scores = [p.score for p in progress_records if p.score is not None]
        
        if not scores:
            return {
                "average_score": None,
                "total_activities": len(progress_records),
                "completed_activities": 0,
                "mastery_level": "Not enough data"
            }
        
        completed_count = sum(
            1 for p in progress_records 
            if p.status in (CompletionStatus.COMPLETED, CompletionStatus.MASTERED)
        )
        
        mastery_count = sum(
            1 for p in progress_records if p.status == CompletionStatus.MASTERED
        )
        
        avg_score = sum(scores) / len(scores)
        
        # Determine mastery level
        if avg_score >= 90 and mastery_count > 5:
            mastery_level = "Expert"
        elif avg_score >= 80:
            mastery_level = "Proficient"
        elif avg_score >= 70:
            mastery_level = "Competent"
        elif avg_score >= 60:
            mastery_level = "Developing"
        else:
            mastery_level = "Beginning"
        
        return {
            "average_score": round(avg_score, 1),
            "total_activities": len(progress_records),
            "completed_activities": completed_count,
            "mastery_level": mastery_level
        }
    
    def _calculate_topic_performance(self, progress_records: List[Progress]) -> List[Dict]:
        """Calculate performance metrics by topic."""
        # Group progress by topic
        topic_progress = {}
        
        for progress in progress_records:
            if not progress.content:
                continue
                
            topic_id = progress.content.topic_id
            if topic_id not in topic_progress:
                topic_progress[topic_id] = []
            
            topic_progress[topic_id].append(progress)
        
        # Calculate metrics for each topic
        result = []
        for topic_id, records in topic_progress.items():
            topic = self.db.query(CurriculumTopic).filter_by(id=topic_id).first()
            if not topic:
                continue
                
            scores = [p.score for p in records if p.score is not None]
            if not scores:
                continue
                
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            
            completed = sum(
                1 for p in records 
                if p.status in (CompletionStatus.COMPLETED, CompletionStatus.MASTERED)
            )
            total = len(records)
            
            result.append({
                "topic_id": topic_id,
                "topic_name": topic.name,
                "average_score": round(avg_score, 1),
                "highest_score": round(max_score, 1),
                "completion_rate": round(completed / total * 100 if total > 0 else 0, 1),
                "activity_count": total
            })
        
        # Sort by average score (descending)
        return sorted(result, key=lambda x: x["average_score"], reverse=True)
    
    def _identify_strengths_weaknesses(self, progress_records: List[Progress]) -> Dict:
        """Identify areas of strength and weakness based on performance data."""
        # Group by content type
        type_performance = {}
        
        for progress in progress_records:
            if not progress.content or progress.score is None:
                continue
                
            content_type = progress.content.content_type
            if content_type not in type_performance:
                type_performance[content_type] = []
            
            type_performance[content_type].append(progress.score)
        
        # Calculate average score by content type
        strengths = []
        weaknesses = []
        
        for content_type, scores in type_performance.items():
            if not scores:
                continue
                
            avg_score = sum(scores) / len(scores)
            item = {
                "content_type": content_type.value,
                "average_score": round(avg_score, 1),
                "activity_count": len(scores)
            }
            
            if avg_score >= 75:
                strengths.append(item)
            elif avg_score < 60:
                weaknesses.append(item)
        
        # Sort strengths and weaknesses
        strengths = sorted(strengths, key=lambda x: x["average_score"], reverse=True)
        weaknesses = sorted(weaknesses, key=lambda x: x["average_score"])
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
    def _analyze_learning_patterns(self, progress_records: List[Progress]) -> Dict:
        """Analyze patterns in learning behavior and progress over time."""
        # Group activities by date
        daily_activity = {}
        
        for progress in progress_records:
            if not progress.last_interaction:
                continue
                
            date_key = progress.last_interaction.strftime("%Y-%m-%d")
            if date_key not in daily_activity:
                daily_activity[date_key] = []
            
            daily_activity[date_key].append(progress)
        
        # Calculate daily metrics
        daily_metrics = []
        
        for date_key, activities in sorted(daily_activity.items()):
            scores = [p.score for p in activities if p.score is not None]
            avg_score = sum(scores) / len(scores) if scores else None
            
            total_time = sum(p.time_spent_seconds for p in activities if p.time_spent_seconds)
            
            daily_metrics.append({
                "date": date_key,
                "activity_count": len(activities),
                "average_score": round(avg_score, 1) if avg_score is not None else None,
                "total_time_minutes": round(total_time / 60, 1) if total_time else 0
            })
        
        # Calculate preferred time patterns (if timestamps available)
        morning_count = afternoon_count = evening_count = 0
        
        for progress in progress_records:
            if not progress.last_interaction:
                continue
                
            hour = progress.last_interaction.hour
            
            if 5 <= hour < 12:
                morning_count += 1
            elif 12 <= hour < 17:
                afternoon_count += 1
            else:
                evening_count += 1
        
        total_with_time = morning_count + afternoon_count + evening_count
        
        time_distribution = {
            "morning": round(morning_count / total_with_time * 100 if total_with_time else 0, 1),
            "afternoon": round(afternoon_count / total_with_time * 100 if total_with_time else 0, 1),
            "evening": round(evening_count / total_with_time * 100 if total_with_time else 0, 1)
        }
        
        return {
            "daily_activity": daily_metrics[-7:],  # Last 7 days
            "time_distribution": time_distribution,
            "total_learning_time_minutes": round(
                sum(p.time_spent_seconds for p in progress_records if p.time_spent_seconds) / 60, 
                1
            )
        }
    
    def _calculate_engagement_metrics(self, progress_records: List[Progress]) -> Dict:
        """Calculate user engagement metrics."""
        # Get unique dates with activity
        active_dates = set()
        last_active = None
        total_activities = len(progress_records)
        
        for progress in progress_records:
            if not progress.last_interaction:
                continue
                
            active_dates.add(progress.last_interaction.date())
            
            if last_active is None or progress.last_interaction > last_active:
                last_active = progress.last_interaction
        
        # Count consecutive days (if any)
        consecutive_days = 0
        if active_dates:
            sorted_dates = sorted(active_dates, reverse=True)
            consecutive_days = 1
            
            for i in range(1, len(sorted_dates)):
                if sorted_dates[i-1] - sorted_dates[i] == timedelta(days=1):
                    consecutive_days += 1
                else:
                    break
        
        # Is currently active?
        is_active = False
        if last_active:
            days_since_active = (datetime.utcnow() - last_active).days
            is_active = days_since_active < 7
        
        # Calculate completion rate
        completed = sum(
            1 for p in progress_records 
            if p.status in (CompletionStatus.COMPLETED, CompletionStatus.MASTERED)
        )
        completion_rate = round(completed / total_activities * 100 if total_activities > 0 else 0, 1)
        
        # Average engagement score
        engagement_scores = [
            p.engagement_score for p in progress_records if p.engagement_score is not None
        ]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else None
        
        return {
            "active_days": len(active_dates),
            "consecutive_days": consecutive_days,
            "is_currently_active": is_active,
            "days_since_last_activity": (datetime.utcnow() - last_active).days if last_active else None,
            "completion_rate": completion_rate,
            "average_engagement_score": round(avg_engagement * 100, 1) if avg_engagement else None
        }
    
    def _generate_recommendations(
        self,
        user: User,
        progress_records: List[Progress],
        strengths_weaknesses: Dict,
        engagement_metrics: Dict
    ) -> List[str]:
        """Generate personalized recommendations based on performance analysis."""
        recommendations = []
        
        # Recommend based on identified weaknesses
        if strengths_weaknesses.get("weaknesses"):
            weak_areas = [w["content_type"] for w in strengths_weaknesses["weaknesses"]]
            
            if ContentType.QUIZ.value in weak_areas:
                recommendations.append(
                    "Practice more quizzes to improve test-taking skills."
                )
            
            if ContentType.EXERCISE.value in weak_areas:
                recommendations.append(
                    "Spend more time on practice exercises for hands-on improvement."
                )
            
            if ContentType.GAME.value in weak_areas:
                recommendations.append(
                    "Try more interactive games to reinforce concepts in a fun way."
                )
        
        # Recommend based on engagement patterns
        if engagement_metrics.get("completion_rate", 0) < 70:
            recommendations.append(
                "Try to complete more of the activities you start for better learning progress."
            )
        
        if engagement_metrics.get("consecutive_days", 0) < 3:
            recommendations.append(
                "Aim for a daily learning streak to build consistency and retention."
            )
        
        if not engagement_metrics.get("is_currently_active", False):
            recommendations.append(
                "It's been a while! Regular practice helps retain math concepts better."
            )
        
        # Topic-specific recommendations
        topic_records = {}
        for progress in progress_records:
            if not progress.content:
                continue
                
            topic_id = progress.content.topic_id
            if topic_id not in topic_records:
                topic_records[topic_id] = []
            topic_records[topic_id].append(progress)
        
        for topic_id, records in topic_records.items():
            scores = [p.score for p in records if p.score is not None]
            if not scores:
                continue
            
            avg_score = sum(scores) / len(scores)
            topic = self.db.query(CurriculumTopic).filter_by(id=topic_id).first()
            
            if topic and avg_score < 60:
                recommendations.append(
                    f"Focus on improving your understanding of '{topic.name}' concepts."
                )
        
        # Limit to top 5 recommendations
        if len(recommendations) > 5:
            recommendations = recommendations[:5]
        
        # Add a positive recommendation if doing well
        if not recommendations and engagement_metrics.get("completion_rate", 0) > 80:
            recommendations.append(
                "You're doing great! Consider trying more challenging content to continue growing."
            )
        
        return recommendations
