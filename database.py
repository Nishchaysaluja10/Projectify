# database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

db = SQLAlchemy()

class Repository(db.Model):
    __tablename__ = 'repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    github_url = db.Column(db.String(255), nullable=False, unique=True, index=True)
    
    # State tracking for the tree-sitter extraction process
    status = db.Column(
        db.Enum('pending_parsing', 'parsed', 'failed_parsing', name='repo_parsing_status'), 
        default='pending_parsing'
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cascade deletion: if a repo link is removed, wipe all its structural nodes
    nodes = db.relationship('ProjectNode', backref='repository', lazy=True, cascade="all, delete-orphan")

class ProjectNode(db.Model):
    __tablename__ = 'project_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    
    node_name = db.Column(db.String(255), nullable=False)
    node_type = db.Column(db.Enum('global', 'class', 'function', name='node_type'), nullable=False)
    
    # Stores the raw code block corresponding to this specific structural node
    code_content = db.Column(db.Text, nullable=False)
    
    # PostgreSQL JSONB column for structural relationships (inbound/outbound code edges)
    # Example format: {"inbound_calls": ["fetchData"], "outbound_calls": ["renderGraph", "logError"]}
    structural_metadata = db.Column(JSONB, nullable=True)
    
    # Composite index to instantly fetch structural nodes belonging to a specific repository
    __table_args__ = (db.Index('idx_repo_nodes', 'repository_id', 'node_type'),)