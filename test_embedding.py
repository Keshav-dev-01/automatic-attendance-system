#!/usr/bin/env python
import os
from attendance_app.app import create_app
from attendance_app.utils.photo import extract_face_embedding
from attendance_app.models.user import Student
from attendance_app.extensions import db

app = create_app()
with app.app_context():
    students = Student.query.all()
    
    if not students:
        print("No students found!")
    else:
        student = students[0]
        print(f"Testing with student: {student.student_id}")
        print(f"Photo embedding: {student.photo_embedding}")
        
        # Test embedding comparison
        if student.photo_embedding and student.photos:
            stored_emb = student.photo_embedding
            photo_emb = student.photos[0].photo_embedding
            
            print(f"\nStored embedding: {stored_emb[:30]}...")
            print(f"Photo embedding: {photo_emb[:30]}...")
            
            if stored_emb == photo_emb:
                print("✓ Embeddings match - they should (same photo)")
            else:
                print("✗ Embeddings differ (this is expected if photos are different)")
