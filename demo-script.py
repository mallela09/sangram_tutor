# demo_script.py
"""
Demo script for Sangram Tutor prototype.

This script simulates student interactions with the system and demonstrates
the adaptive learning capabilities, personalization, and analytics.
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timedelta

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

# Configuration
BASE_URL = "http://127.0.0.1:8080/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
STUDENT_CREDENTIALS = {"username": "student", "password": "student123"}


def login(credentials):
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data=credentials
    )
    response.raise_for_status()
    return response.json()


def get_headers(token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {token}"}


def simulate_student_session(token, headers, session_length=5):
    """Simulate a student learning session."""
    print("\n\n" + "="*80)
    print(" "*30 + "STUDENT LEARNING SESSION")
    print("="*80 + "\n")

    # Step 1: Get user profile
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    user = response.json()
    
    print(f"👋 Hello, {user['full_name'] or user['username']}!")
    print(f"You are in Grade {user['grade_level']}\n")
    
    # Step 2: Get next recommended content
    print("🤖 AI is analyzing your previous performance and learning style...")
    time.sleep(1)
    
    response = requests.get(f"{BASE_URL}/learning/next-content", headers=headers)
    if response.status_code == 404:
        print("No personalized content found. Let's explore available topics.")
        # Get available topics
        response = requests.get(
            f"{BASE_URL}/learning/topics?grade_level={user['grade_level']}", 
            headers=headers
        )
        topics = response.json()
        
        print("\nAvailable topics for your grade:")
        for i, topic in enumerate(topics):
            print(f"{i+1}. {topic['name']}")
        
        # Select first topic
        selected_topic = topics[0]
        print(f"\nLet's start with '{selected_topic['name']}'")
        
        # Get content for the topic
        response = requests.get(
            f"{BASE_URL}/learning/topics/{selected_topic['id']}/content", 
            headers=headers
        )
        content_items = response.json()
        
        # Start with the first content
        content = content_items[0]
    else:
        content = response.json()
    
    # Simulate going through multiple content items
    for _ in range(session_length):
        print("\n" + "-"*80)
        print(f"📚 {content['title']} ({content['content_type'].capitalize()})")
        print(f"Difficulty: {content['difficulty_level'].capitalize()}")
        print("-"*80)
        
        # Display content sample based on type
        content_data = content['content_data']
        
        if content['content_type'] == 'concept':
            for element in content_data.get('elements', [])[:2]:
                if element.get('type') == 'text':
                    print(f"\n{element.get('content')}")
        
        elif content['content_type'] == 'exercise':
            problems = content_data.get('problems', [])
            if problems:
                print("\nSample problems:")
                for i, problem in enumerate(problems[:2]):
                    print(f"  {i+1}. {problem.get('prompt')}")
        
        elif content['content_type'] == 'game':
            print(f"\nGame type: {content_data.get('game_type', 'interactive')}")
            print("Game elements: Interactive learning through play")
        
        elif content['content_type'] == 'quiz':
            questions = content_data.get('questions', [])
            if questions:
                print("\nSample questions:")
                for i, question in enumerate(questions[:2]):
                    print(f"  {i+1}. {question.get('prompt')}")
        
        # Simulate student engagement
        print("\n👩‍🎓 Student is engaging with the content...")
        engagement_time = random.randint(2, 5)  # minutes
        time.sleep(1)  # Just for demo flow
        
        # Simulate performance
        score = random.uniform(60, 95)
        engagement_score = random.uniform(0.6, 0.9)
        status = "completed"
        
        # Update progress
        progress_data = {
            "status": status,
            "score": round(score, 1),
            "time_spent_seconds": engagement_time * 60,
            "engagement_score": round(engagement_score, 2),
            "mistakes_data": {"common_errors": ["calculation_error", "concept_misunderstanding"]},
            "notes": "Student showed good engagement"
        }
        
        response = requests.post(
            f"{BASE_URL}/learning/content/{content['id']}/progress",
            json=progress_data,
            headers=headers
        )
        progress = response.json()
        
        # Display results
        print(f"\n✅ Completed with score: {progress_data['score']}%")
        print(f"⏱️ Time spent: {engagement_time} minutes")
        
        # AI feedback based on performance
        print("\n🤖 AI Tutor Feedback:")
        if score >= 90:
            print("  Excellent work! You've mastered this concept.")
            print("  Let's move on to something more challenging.")
        elif score >= 75:
            print("  Good job! You're understanding the concept well.")
            print("  Let's practice a bit more to reinforce your learning.")
        elif score >= 60:
            print("  You're on the right track, but need more practice.")
            print("  Let's focus on the areas where you made mistakes.")
        else:
            print("  Let's review this concept again in a different way.")
            print("  I'll break it down into smaller steps for you.")
        
        # Get next content
        response = requests.get(f"{BASE_URL}/learning/next-content", headers=headers)
        if response.status_code == 200:
            content = response.json()
        else:
            print("\n🎉 You've completed all available content in this learning path!")
            break
    
    print("\n" + "="*80)
    print(" "*30 + "SESSION COMPLETE")
    print("="*80)


def show_learning_analytics(token, headers):
    """Display learning analytics dashboard."""
    print("\n\n" + "="*80)
    print(" "*25 + "STUDENT LEARNING ANALYTICS")
    print("="*80 + "\n")
    
    # Get performance analytics
    response = requests.get(f"{BASE_URL}/analytics/performance", headers=headers)
    analytics = response.json()
    
    # Display overall performance
    overall = analytics.get('overall_score', {})
    print("📊 Overall Performance")
    print(f"Average Score: {overall.get('average_score', 'N/A')}%")
    print(f"Completed Activities: {overall.get('completed_activities', 0)}/{overall.get('total_activities', 0)}")
    print(f"Mastery Level: {overall.get('mastery_level', 'Beginning')}")
    
    # Display topic performance
    topics = analytics.get('topic_performance', [])
    if topics:
        print("\n📚 Performance by Topic")
        topic_data = []
        for topic in topics:
            topic_data.append([
                topic.get('topic_name'),
                f"{topic.get('average_score')}%",
                f"{topic.get('completion_rate')}%",
                topic.get('activity_count')
            ])
        
        print(tabulate(
            topic_data,
            headers=["Topic", "Avg Score", "Completion", "Activities"],
            tablefmt="simple"
        ))
    
    # Display strengths and weaknesses
    strengths = analytics.get('strengths_weaknesses', {}).get('strengths', [])
    weaknesses = analytics.get('strengths_weaknesses', {}).get('weaknesses', [])
    
    if strengths:
        print("\n💪 Strengths")
        for item in strengths:
            print(f"- {item.get('content_type').capitalize()}: {item.get('average_score')}%")
    
    if weaknesses:
        print("\n🔍 Areas for Improvement")
        for item in weaknesses:
            print(f"- {item.get('content_type').capitalize()}: {item.get('average_score')}%")
    
    # Display learning patterns
    patterns = analytics.get('learning_patterns', {})
    if patterns:
        print("\n⏱️ Learning Patterns")
        print(f"Total Learning Time: {patterns.get('total_learning_time_minutes', 0)} minutes")
        
        # Display time distribution
        time_dist = patterns.get('time_distribution', {})
        if time_dist:
            print("\nPreferred Learning Times:")
            print(f"- Morning: {time_dist.get('morning', 0)}%")
            print(f"- Afternoon: {time_dist.get('afternoon', 0)}%")
            print(f"- Evening: {time_dist.get('evening', 0)}%")
    
    # Display engagement metrics
    engagement = analytics.get('engagement_metrics', {})
    if engagement:
        print("\n🎯 Engagement Metrics")
        print(f"Active Days: {engagement.get('active_days', 0)}")
        print(f"Current Streak: {engagement.get('consecutive_days', 0)} days")
        print(f"Completion Rate: {engagement.get('completion_rate', 0)}%")
        if engagement.get('average_engagement_score'):
            print(f"Engagement Score: {engagement.get('average_engagement_score')}%")
    
    # Display recommendations
    recommendations = analytics.get('recommendations', [])
    if recommendations:
        print("\n💡 Personalized Recommendations")
        for i, rec in enumerate(recommendations):
            print(f"{i+1}. {rec}")
    
    print("\n" + "="*80)


def show_learning_styles(token, headers):
    """Display learning style analysis."""
    print("\n\n" + "="*80)
    print(" "*25 + "LEARNING STYLE ANALYSIS")
    print("="*80 + "\n")
    
    # Get learning style predictions
    response = requests.get(f"{BASE_URL}/learning/learning-styles", headers=headers)
    styles = response.json()
    
    if not styles:
        print("Not enough data to analyze learning styles yet.")
        return
    
    print("🧠 Your Learning Style Profile")
    print("\nThe AI has analyzed your learning patterns and identified your preferences:")
    
    # Sort styles by strength
    sorted_styles = sorted(styles.items(), key=lambda x: x[1], reverse=True)
    
    # Display style strength bars
    max_label_len = max(len(style.replace('_', ' ').title()) for style, _ in sorted_styles)
    
    for style, value in sorted_styles:
        label = style.replace('_', ' ').title()
        bar_length = int(value * 20)  # Scale to 0-20 characters
        spaces = max_label_len - len(label)
        print(f"{label}:{' ' * spaces} {'█' * bar_length} ({value:.2f})")
    
    # Provide interpretation of top styles
    print("\n✨ What This Means For You")
    
    top_style = sorted_styles[0][0]
    if top_style == 'visual':
        print("You learn best through visual elements like diagrams, charts, and images.")
        print("The app will prioritize visual content and representations for you.")
    elif top_style == 'auditory':
        print("You learn best through listening and verbal explanations.")
        print("The app will include more audio explanations and verbal instruction.")
    elif top_style == 'reading_writing':
        print("You learn best through reading and writing information.")
        print("The app will provide more text-based content and note-taking activities.")
    elif top_style == 'kinesthetic':
        print("You learn best through hands-on activities and interactive exercises.")
        print("The app will prioritize interactive games and practical applications.")
    elif top_style == 'logical':
        print("You learn best through logical reasoning and systematic thinking.")
        print("The app will focus on problem-solving and pattern recognition.")
    elif top_style == 'social':
        print("You learn best in collaborative settings and group activities.")
        print("The app will include more collaborative challenges when possible.")
    elif top_style == 'solitary':
        print("You learn best through independent study and self-paced learning.")
        print("The app will provide more self-directed activities and reflection.")
    
    print("\n" + "="*80)


def show_content_recommendations(token, headers):
    """Display personalized content recommendations."""
    print("\n\n" + "="*80)
    print(" "*25 + "PERSONALIZED RECOMMENDATIONS")
    print("="*80 + "\n")
    
    # Get recommendations
    response = requests.get(f"{BASE_URL}/learning/recommendations", headers=headers)
    if response.status_code != 200:
        print("No personalized recommendations available yet.")
        return
    
    recommendations = response.json()
    
    print("🎯 Recommended Just For You")
    print("\nBased on your performance, learning style, and interests, we recommend:")
    
    for i, rec in enumerate(recommendations):
        print(f"\n{i+1}. {rec.get('title')}")
        print(f"   Type: {rec.get('content_type', '').capitalize()}")
        print(f"   Difficulty: {rec.get('difficulty_level', '').capitalize()}")
        print(f"   Relevance: {rec.get('relevance_score', 0):.1f}%")
        if rec.get('recommendation_reason'):
            print(f"   Why: {rec.get('recommendation_reason')}")
    
    print("\n" + "="*80)


def simulate_parent_view(token, headers):
    """Simulate parent dashboard view."""
    print("\n\n" + "="*80)
    print(" "*30 + "PARENT DASHBOARD")
    print("="*80 + "\n")
    
    # Get student performance
    response = requests.get(f"{BASE_URL}/analytics/performance", headers=headers)
    analytics = response.json()
    
    print("👨‍👩‍👧‍👦 Parent View: Child's Progress")
    
    # Overall progress summary
    overall = analytics.get('overall_score', {})
    print(f"\nOverall Progress: {overall.get('mastery_level', 'Beginning')}")
    print(f"Average Score: {overall.get('average_score', 'N/A')}%")
    print(f"Completed Activities: {overall.get('completed_activities', 0)}/{overall.get('total_activities', 0)}")
    
    # Weekly activity summary
    patterns = analytics.get('learning_patterns', {})
    daily_activity = patterns.get('daily_activity', [])
    
    if daily_activity:
        print("\n📅 Weekly Activity")
        activity_data = []
        for day in daily_activity:
            activity_data.append([
                day.get('date', 'N/A'),
                day.get('activity_count', 0),
                f"{day.get('average_score', 0)}%" if day.get('average_score') else 'N/A',
                f"{day.get('total_time_minutes', 0)} min"
            ])
        
        print(tabulate(
            activity_data,
            headers=["Date", "Activities", "Avg Score", "Time Spent"],
            tablefmt="simple"
        ))
    
    # Topic progress
    topics = analytics.get('topic_performance', [])
    if topics:
        print("\n📚 Topic Progress")
        for topic in topics[:3]:  # Show top 3 topics
            print(f"- {topic.get('topic_name')}: {topic.get('average_score')}% ({topic.get('completion_rate')}% complete)")
    
    # Recommendations for parents
    print("\n💡 Suggestions for Parents:")
    
    weaknesses = analytics.get('strengths_weaknesses', {}).get('weaknesses', [])
    if weaknesses:
        weak_type = weaknesses[0].get('content_type', '').capitalize()
        print(f"1. Help your child with {weak_type} activities to boost confidence.")
    
    engagement = analytics.get('engagement_metrics', {})
    if engagement.get('consecutive_days', 0) < 3:
        print("2. Encourage daily practice to build consistent learning habits.")
    
    print("3. Ask your child to explain what they learned today to reinforce concepts.")
    print("4. Celebrate their achievements to maintain motivation.")
    
    print("\n" + "="*80)


def run_demo():
    """Run the complete demo."""
    print("\n" + "="*80)
    print(" "*25 + "SANGRAM TUTOR AI DEMO")
    print("="*80)
    print("\nInitializing demo...\n")
    
    try:
        # Login as student
        print("Logging in as student...")
        student_token_data = login(STUDENT_CREDENTIALS)
        student_token = student_token_data['access_token']
        student_headers = get_headers(student_token)
        
        # Simulate student learning session
        simulate_student_session(student_token, student_headers, session_length=3)
        
        # Show learning analytics
        show_learning_analytics(student_token, student_headers)
        
        # Show learning styles
        show_learning_styles(student_token, student_headers)
        
        # Show content recommendations
        show_content_recommendations(student_token, student_headers)
        
        # Login as parent
        print("\nLogging in as parent...")
        parent_credentials = {"username": "parent", "password": "parent123"}
        parent_token_data = login(parent_credentials)
        parent_token = parent_token_data['access_token']
        parent_headers = get_headers(parent_token)
        
        # Show parent view
        simulate_parent_view(parent_token, parent_headers)
        
        print("\nDemo completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API server.")
        print("Make sure the server is running at http://localhost:8080")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sangram Tutor Demo")
    parser.add_argument("--url", help="API base URL", default="http://127.0.0.1:8080/api")
    
    args = parser.parse_args()
    BASE_URL = args.url
    
    run_demo()
