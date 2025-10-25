from __future__ import annotations

import logging
from typing import Optional

from firebase_admin import firestore

from app.domain.users import User
from app.application.contracts.repositories import UserRepository
from app.infrastructure.services.firebase_admin import initialize_firebase_app

logger = logging.getLogger(__name__)

class FirestoreUserRepository(UserRepository):
    def __init__(self) -> None:
        try:
            app = initialize_firebase_app()
            self.db = firestore.client(app)
            self.users_collection = self.db.collection('users')
            logger.info("Successfully connected to Firestore - Users Collection")
        except Exception as e:
            logger.error(f"Error connecting to Firestore: {e}")
            raise

    def get_by_id(self, user_id: str) -> Optional[User]:
        doc = self.users_collection.document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        return User(
            id=doc.id,
            email=data["email"],
            hashed_password=data["hashed_password"],
        )

    def get_by_email(self, email: str) -> Optional[User]:
        query = self.users_collection.where("email", "==", email).limit(1).get()
        docs = list(query)
        if not docs:
            return None
        data = docs[0].to_dict()
        return User(
            id=docs[0].id,
            email=data["email"],
            hashed_password=data["hashed_password"],
        )

    def add(self, user: User) -> None:
        self.users_collection.document(user.id).set({
            "email": user.email,
            "hashed_password": user.hashed_password,
        })