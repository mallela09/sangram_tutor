# Import all models for easy access
from models.base import Base
from models.user import User, UserRole
from models.curriculum import (
    CurriculumTopic, CurriculumContent, 
    Subject, ContentType, DifficultyLevel
)
from models.progress import (
    LearningProgress, TopicProgress, 
    LearningSession, SessionProgress
)
from models.achievements import (
    Achievement, UserAchievement,
    AchievementType
)
from models.learning_path import (
    LearningPath, PathRecommendation
)
from models.recommendation import (
    Recommendation, RecommendationFeedback,
    RecommendationType
)
from models.learning_style_detector import (
    LearningStyle, LearningInteraction
)

# This allows for easy imports like:
# from models import User, UserRole