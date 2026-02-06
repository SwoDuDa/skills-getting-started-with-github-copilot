"""Tests for the High School Management System API endpoints."""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to the static index page."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        assert "Soccer Team" in activities
        assert "Basketball Club" in activities
        assert "Programming Class" in activities
    
    def test_get_activities_has_correct_structure(self, client):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        activities = response.json()
        
        soccer_team = activities["Soccer Team"]
        assert "description" in soccer_team
        assert "schedule" in soccer_team
        assert "max_participants" in soccer_team
        assert "participants" in soccer_team
        assert isinstance(soccer_team["participants"], list)
        assert soccer_team["max_participants"] == 25


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_student_success(self, client):
        """Test successful signup of a new student."""
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Soccer Team" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Soccer Team"]["participants"]
    
    def test_signup_duplicate_student_fails(self, client):
        """Test that signing up the same student twice fails."""
        email = "alex@mergington.edu"
        
        # Try to signup student who is already registered
        response = client.post(
            f"/activities/Soccer Team/signup?email={email}"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity fails."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_with_url_encoded_activity_name(self, client):
        """Test signup with URL-encoded activity name."""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newchessplayer@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "Chess Club" in data["message"]
    
    def test_signup_multiple_students_to_different_activities(self, client):
        """Test signing up multiple students to different activities."""
        students = [
            ("student1@mergington.edu", "Art Studio"),
            ("student2@mergington.edu", "Drama Club"),
            ("student3@mergington.edu", "Debate Team"),
        ]
        
        for email, activity in students:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all students were added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        for email, activity in students:
            assert email in activities[activity]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_existing_student_success(self, client):
        """Test successful unregistration of an existing student."""
        email = "alex@mergington.edu"
        
        # Verify student is registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Soccer Team"]["participants"]
        
        # Unregister student
        response = client.delete(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Unregistered" in data["message"] or "unregistered" in data["message"].lower()
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Soccer Team"]["participants"]
    
    def test_unregister_non_registered_student_fails(self, client):
        """Test that unregistering a non-registered student fails."""
        response = client.delete(
            "/activities/Soccer Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test that unregistering from a non-existent activity fails."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_with_url_encoded_activity_name(self, client):
        """Test unregister with URL-encoded activity name."""
        email = "james@mergington.edu"
        
        response = client.delete(
            f"/activities/Basketball%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Basketball Club"]["participants"]


class TestSignupAndUnregisterWorkflow:
    """Integration tests for signup and unregister workflows."""
    
    def test_signup_then_unregister_workflow(self, client):
        """Test the complete workflow of signing up and then unregistering."""
        email = "workflow@mergington.edu"
        activity = "Chess Club"
        
        # 1. Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # 2. Verify signup
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
        
        # 3. Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # 4. Verify unregistration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple signup and unregister operations."""
        activity = "Programming Class"
        emails = [
            "programmer1@mergington.edu",
            "programmer2@mergington.edu",
            "programmer3@mergington.edu"
        ]
        
        # Sign up all students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all are registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        for email in emails:
            assert email in activities[activity]["participants"]
        
        # Unregister first student
        response = client.delete(
            f"/activities/{activity}/unregister?email={emails[0]}"
        )
        assert response.status_code == 200
        
        # Verify first student removed, others remain
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert emails[0] not in activities[activity]["participants"]
        assert emails[1] in activities[activity]["participants"]
        assert emails[2] in activities[activity]["participants"]
