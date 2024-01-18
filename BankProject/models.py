from BankProject import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(), unique = True, nullable = False)
    email = db.Column(db.String(), unique = True, nullable = False)
    password = db.Column(db.String(), nullable = False)
    transactions = db.relationship('Transaction', backref='user', lazy = True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Transaction(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    price = db.Column(db.Integer(), nullable = False)
    category = db.Column(db.String(), nullable = False)
    date = db.Column(db.String(), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Transaction Category('{self.category}')"

