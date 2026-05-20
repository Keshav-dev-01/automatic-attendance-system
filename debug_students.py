#!/usr/bin/env python
from attendance_app.app import create_app
from attendance_app.models.user import Student, StudentPhoto
from attendance_app.extensions import db

app = create_app()
with app.app_context():
    students = Student.query.all()
    print(f'Total students: {len(students)}')
    for s in students:
        has_embed = 'Yes' if s.photo_embedding else 'No'
        photo_count = len(s.photos)
        print(f'  Student ID: {s.student_id}, Main Embedding: {has_embed}, Photo Count: {photo_count}')
        if s.photo_embedding:
            print(f'    - Main embedding: {s.photo_embedding[:20]}...')
        for i, p in enumerate(s.photos):
            emb_preview = p.photo_embedding[:20] + '...' if p.photo_embedding else 'None'
            print(f'    - Photo {i+1} embedding: {emb_preview}')
