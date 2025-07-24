from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from geopy.geocoders import Nominatim
from sqlalchemy import func, text
from collections import defaultdict
from datetime import datetime,date
from sqlalchemy.exc import IntegrityError
import re
from functools import wraps
from flask import abort
from werkzeug.security import generate_password_hash
import os
from flask_wtf import CSRFProtect


app = Flask(__name__)




app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ecommerce.db')
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user') 

class NGO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    contact_person = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))

    # Relationships
    teams = db.relationship('Team', backref='ngo', cascade="all, delete", passive_deletes=True)
    donations = db.relationship('Donation', backref='ngo', cascade="all, delete", passive_deletes=True)
    #inventories = db.relationship('Inventory', backref='ngo', lazy=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(255), nullable=False)
    team_leader = db.Column(db.String(255), nullable=False)
    equipment = db.Column(db.String(255), nullable=True)
    personnel = db.Column(db.Integer, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngo.id', ondelete='CASCADE'),nullable=False)
    __table_args__ = (
        db.UniqueConstraint('team_name', 'team_leader', 'task_id', name='uq_team_name_leader_global'),
    )

    def __repr__(self):
        return f"<Team {self.team_name}>"
    
class Task(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(255), nullable=False)

    event_id = db.Column(db.Integer, db.ForeignKey('emergency_event.id'), nullable=False)

    # Relationship to teams
    teams = db.relationship('Team', backref='task', lazy=True)

    def __repr__(self):
        return f"<Task {self.task_name}>"

class Evacuation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transport = db.Column(db.String(255))
    location = db.Column(db.String(255))
    destination = db.Column(db.String(255))

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('emergency_event.id', ondelete='CASCADE'))

    team = db.relationship('Team', backref='evacuations')
   


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngo.id',ondelete='CASCADE'),nullable=False)
    def __repr__(self):
        return f"<Donation {self.name}>"



class EmergencyEvent(db.Model):
    __tablename__ = 'emergency_event'
    id = db.Column(db.Integer, primary_key=True)
    disaster_type = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.String(255), nullable=False)
    affected_area = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    victims = db.relationship('Victim', backref='disaster', cascade="all, delete-orphan")
    evacuations = db.relationship('Evacuation', backref='event', cascade='all, delete-orphan')

    tasks = db.relationship('Task', backref='event', lazy=True)
   
    __table_args__ = (
        db.UniqueConstraint('disaster_type', 'start_date', 'affected_area', name='unique_disaster_event'),
    )

    # one-to-many
    aid_requirements = db.relationship(
        'AidRequirement',
        back_populates='emergency_event',
        cascade='all, delete-orphan'
    )
    inventories = db.relationship(
        'Inventory',
        back_populates='emergency_event',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<EmergencyEvent {self.disaster_type} - {self.affected_area} on {self.start_date}>"

class Victim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    emergency_event_id = db.Column(db.Integer, db.ForeignKey('emergency_event.id'), nullable=False)
    
    

    def __repr__(self):
        return f"<Victim {self.first_name} {self.last_name}>"

class AidRequirement(db.Model):
    __tablename__ = 'aid_requirement'
    id = db.Column(db.Integer, primary_key=True)
    food_needed = db.Column(db.Integer, nullable=False)
    water_needed = db.Column(db.Integer, nullable=False)
    medical_needed = db.Column(db.Integer, nullable=False)
    emergency_event_id = db.Column(
        db.Integer,
        db.ForeignKey('emergency_event.id', ondelete='CASCADE'),
        nullable=False
    )

    emergency_event = db.relationship(
        'EmergencyEvent',
        back_populates='aid_requirements'
    )

    def __repr__(self):
        return f"<AidRequirement for event {self.emergency_event_id}>"


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    minimum_required = db.Column(db.Integer, nullable=True)
    disaster_id = db.Column(
        db.Integer,
        db.ForeignKey('emergency_event.id', ondelete='CASCADE'),
        nullable=False
    )

    emergency_event = db.relationship(
        'EmergencyEvent',
        back_populates='inventories'
    )

    def __repr__(self):
        return f"<Inventory {self.item_name} ({self.quantity})>"

class InventoryView(db.Model):
    __tablename__ = 'inventory_view'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String)
    quantity = db.Column(db.Integer)
    minimum_required = db.Column(db.Integer)
    disaster_type = db.Column(db.String)
    affected_area = db.Column(db.String)

    # Mark read-only if needed
    def __repr__(self):
        return f"<InventoryView {self.item_name} - {self.disaster_type}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


@app.route('/manage-users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/update-role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['admin', 'user']:
        user.role = new_role
        db.session.commit()
        flash(f"{user.email}'s role updated to {new_role}", 'success')
    return redirect(url_for('manage_users'))

@app.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.email} has been deleted.", 'success')
    return redirect(url_for('manage_users'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.', 'login_error')
        return render_template('login.html')
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # ✅ Email uniqueness check
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('register.html')

        # ✅ Password validation
        if not re.fullmatch(r'[A-Za-z0-9]{8,}', password):
            flash('Password must be at least 8 characters long and contain only letters and numbers.', 'error')
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=email,
            password=hashed_password,
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
   

    return render_template('register.html')



@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch raw events if you need to list them:
    events = EmergencyEvent.query.all()

    # Summarize disasters
    disaster_summary = (
        db.session.query(
            EmergencyEvent.disaster_type,
            db.func.count(EmergencyEvent.id)
        )
        .group_by(EmergencyEvent.disaster_type)
        .all()
    )
    disaster_labels = [d[0] for d in disaster_summary]
    disaster_counts = [d[1] for d in disaster_summary]

    # Summarize donations
    donation_summary = (
        db.session.query(
            Donation.type,
            db.func.count(Donation.id)
        )
        .group_by(Donation.type)
        .all()
    )
    donation_types = [d[0] for d in donation_summary]
    donation_counts = [d[1] for d in donation_summary]

    # Other aggregates
    active_disasters_count = EmergencyEvent.query.count()
    total_donations_count  = Donation.query.count()
    evacuations_count       = Evacuation.query.count()
    active_teams_count      = Team.query.count()

    return render_template(
        'dashboard.html',
        name=current_user.first_name,
        events=events,
        disaster_labels=disaster_labels,
        disaster_counts=disaster_counts,
        donation_types=donation_types,
        donation_counts=donation_counts,
        active_disasters_count=active_disasters_count,
        total_donations_count=total_donations_count,
        evacuations_count=evacuations_count,
        active_teams_count=active_teams_count
    )


@app.route('/report_disaster', methods=['GET', 'POST'])
@login_required
def report_disaster():
    if request.method == 'POST':
        # Grab the data from the form submission
        disaster_type = request.form['disaster_type']
        start_date = request.form['start_date']
        affected_area = request.form.get('affected_area')
        
         # Validate date is not in the future
        if datetime.strptime(start_date, "%Y-%m-%d").date() > date.today():
            flash("Disaster date cannot be in the future.", "error")
            return redirect(url_for('report_disaster'))
        
         # Geocode the affected_area to get lat and lng
        geolocator = Nominatim(user_agent="your_app_name")
        location = geolocator.geocode(affected_area)

        if location:
            latitude = location.latitude
            longitude = location.longitude
        else:
            latitude = None
            longitude = None

        existing_event = EmergencyEvent.query.filter_by(
            disaster_type=disaster_type,
            start_date=start_date,
            affected_area=affected_area
        ).first()

        if existing_event:
            # If a duplicate is found, flash a message and prevent the insert
            flash('A disaster with the same name, date, and affected area already exists.', 'error')
            return redirect(url_for('report_disaster'))

        # Create a new EmergencyEvent object using the submitted data
        new_event = EmergencyEvent(disaster_type=disaster_type, start_date=start_date,affected_area=affected_area,latitude=latitude,
            longitude=longitude)

        # Add the new event to the database
        try:
            db.session.add(new_event)
            db.session.commit()
            flash('Disaster reported successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('A disaster with the same type, date, and location already exists.', 'error')
            
        return redirect(url_for('dashboard'))

    # If GET request, simply render the disaster reporting form
    return render_template('report_disaster.html')

@app.route('/emergency_events')
@login_required
def emergency_events():
    # Fetch all the emergency events from the database
    events = EmergencyEvent.query.all()
    
    disaster_summary = db.session.query(
        EmergencyEvent.disaster_type,
        db.func.count(EmergencyEvent.id)
    ).group_by(EmergencyEvent.disaster_type).all()

    disaster_labels = [d[0] for d in disaster_summary]
    disaster_counts = [d[1] for d in disaster_summary]
    
    # Pass the events to the template to display them
    return render_template('emergency_events.html', events=events, disaster_labels=disaster_labels,
        disaster_counts=disaster_counts)

@app.route('/delete_emergency_event/<int:event_id>', methods=['POST'])
@login_required
@admin_required
def delete_emergency_event(event_id):
    event = EmergencyEvent.query.get_or_404(event_id)
  
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('emergency_events'))

@app.route('/donations', methods=['GET', 'POST'])
@login_required
def donations():
    ngos = NGO.query.all()
    if request.method == 'POST':
        name = request.form['name']
        type_ = request.form['type']
        amount = request.form['amount']
        ngo_id = request.form['ngo_id']

        if not name or not type_ or not amount:
            flash("All fields are required.", "error")
            return redirect(url_for('donations'))
        
        if not amount.isdigit():
            flash('Donation amount must be a number.', 'error')
            return redirect(url_for('donations'))

        amount = int(amount)
        if amount < 1:
            flash('Donation amount must be a positive number.', 'error')
            return redirect(url_for('donations'))

        try:
            new_donation = Donation(name=name, type=type_, amount=int(amount),ngo_id=ngo_id)
            db.session.add(new_donation)
            db.session.commit()
            flash("Donation added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")

        return redirect(url_for('donations'))

    donations = Donation.query.all()
    return render_template('donations.html', donations=donations,ngos=ngos)

@app.route('/delete_donation/<int:donation_id>', methods=['POST'])
@login_required
@admin_required
def delete_donation(donation_id):
    donation = Donation.query.get_or_404(donation_id)
    db.session.delete(donation)
    db.session.commit()
    flash('Donation deleted successfully.', 'success')
    return redirect(request.referrer or url_for('view_donations'))


# Add a new team
@app.route('/add_team', methods=['GET', 'POST'])
@login_required
def add_team():
    if request.method == 'POST':
        team_name = request.form['team_name']
        team_leader = request.form['team_leader']
        equipment = request.form['equipment']
        personnel = request.form['personnel']
        task_id = request.form['task_id']

        existing_team = Team.query.filter_by(
            team_name=team_name,
            team_leader=team_leader,
            task_id=task_id
        ).first()

        if existing_team:
            flash('A team with this name and leader already exists for the selected task.', 'error')
            return redirect(url_for('add_team'))


        new_team = Team(
            team_name=team_name,
            team_leader=team_leader,
            equipment=equipment,
            personnel=personnel,
            task_id=task_id
        )

        db.session.add(new_team)
        db.session.commit()
        flash('Team added successfully.', 'success')
        return redirect(url_for('manage_teams'))

    tasks = Task.query.all()
    return render_template('add_team.html', tasks=tasks)




@app.route('/delete_team/<int:team_id>', methods=['POST'])
@login_required
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    return redirect(url_for('manage_teams'))

# Manage teams route
@app.route('/manage_teams')
@login_required
def manage_teams():
    teams = Team.query.all()
    return render_template('manage_teams.html', teams=teams)

@app.route('/add_victim', methods=['GET', 'POST'])
@login_required
def add_victim():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        location = request.form['location']
        emergency_event_id = request.form['emergency_event_id']  # From form (drop-down or other)

        new_victim = Victim(first_name=first_name, last_name=last_name, age=age, location=location, emergency_event_id=emergency_event_id)

        db.session.add(new_victim)
        db.session.commit()

        flash('Victim added successfully!', 'success')
        return redirect(url_for('view_victims_by_disaster', event_id=emergency_event_id))

    emergency_events = EmergencyEvent.query.all()  # For drop-down selection
    return render_template('add_victim.html', emergency_events=emergency_events)

@app.route('/view_victims/<int:event_id>', methods=['GET'])
@login_required
def view_victim(event_id):
    # Fetch all victims for the selected disaster (event_id)
    event = EmergencyEvent.query.get(event_id)
    victims = Victim.query.filter_by(emergency_event_id=event_id).all()

    return render_template('view_victim.html', victims=victims, event=event)

@app.route('/view_victims_by_disaster')
@login_required
def view_victims_by_disaster():
    events = EmergencyEvent.query.all()
    return render_template('view_victim.html', events=events)


@app.route('/delete_victim/<int:victim_id>', methods=['POST'])
@login_required
@admin_required
def delete_victim(victim_id):
    victim = Victim.query.get_or_404(victim_id)
    db.session.delete(victim)
    db.session.commit()
    flash('Victim deleted successfully!', 'success')
    return redirect(url_for('view_victims_by_disaster'))  # Redirect to the view victims page


@app.route('/inventory_summary')
@login_required
def inventory_summary():
    result = db.session.execute(text("SELECT * FROM inventory_view"))
    inventory_data = result.fetchall()

    grouped_data = defaultdict(list)
    for row in inventory_data:
        key = f"{row.disaster_type} - {row.affected_area}"
        grouped_data[key].append(row)

    return render_template('inventory_summary.html', grouped_data=grouped_data)

@app.route('/add_inventory', methods=['GET', 'POST'])
@login_required
@admin_required
def add_inventory():
    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = int(request.form['quantity'])
        minimum_required = int(request.form['minimum_required'])
        disaster_id = int(request.form['disaster_id'])

        new_item = Inventory(
            item_name=item_name,
            quantity=quantity,
            minimum_required=minimum_required,
            disaster_id=disaster_id
        )
        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('inventory_summary'))

    events = EmergencyEvent.query.all()
    return render_template('add_inventory.html', events=events)




@app.route('/aid_status')
def view_aid_status():
    events = EmergencyEvent.query.all()
    grouped = {}

    for event in events:
        low_stock_items = Inventory.query.filter(
            Inventory.disaster_id == event.id,
            Inventory.quantity < Inventory.minimum_required
        ).all()

        if low_stock_items:
            key = f"{event.disaster_type} - {event.affected_area} (ID: {event.id})"
            grouped[key] = low_stock_items

    return render_template('aid_status.html', grouped_inventory=grouped)



@app.route('/view_inventory')
@login_required
def view_inventory():
    all_inventory = Inventory.query.all()
    inventory_by_disaster = {}

    for item in all_inventory:
        event = EmergencyEvent.query.get(item.disaster_id)
        if event:
            key = f"{event.disaster_type} - {event.affected_area}"
        else:
            key = "Unknown Disaster"

        if key not in inventory_by_disaster:
            inventory_by_disaster[key] = []
        inventory_by_disaster[key].append(item)

    return render_template('view_inventory.html', inventory_by_disaster=inventory_by_disaster)


@app.route('/inventory/reduce/<int:item_id>', methods=['POST'])
@login_required
def reduce_inventory(item_id):
    item = Inventory.query.get_or_404(item_id)
    quantity_used = int(request.form['quantity_used'])

    if quantity_used <= 0:
        flash("Please enter a positive quantity to use.", "error")
    elif quantity_used > item.quantity:
        flash(f"Not enough inventory. Available: {item.quantity}", "error")
    else:
        item.quantity -= quantity_used
        db.session.commit()
        flash(f"Used {quantity_used} of {item.item_name}. Remaining: {item.quantity}", "success")

    return redirect(url_for('inventory_summary'))


@app.route('/delete_inventory/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_inventory(item_id):
    item = Inventory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory_summary'))

@app.route('/create_task', methods=['GET', 'POST'])

@login_required
@admin_required
def create_task():
    events = EmergencyEvent.query.all()

    if request.method == 'POST':
        task_name = request.form['task_name']
        event_id = request.form['event_id']

        task = Task(task_name=task_name, event_id=event_id)
        db.session.add(task)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('create_task.html', events=events)

@app.route('/assign_team', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_team():
    tasks = Task.query.all()
    ngos  = NGO.query.all()

    if request.method == 'POST':
        team_name = request.form['team_name']
        team_leader = request.form['team_leader']
        equipment = request.form.get('equipment')
        personnel = request.form['personnel']
        task_id = request.form['task_id']
        ngo_id = request.form['ngo_id'] 

        # Check if a team with the same name and leader already exists
        duplicate_team = Team.query.filter_by(team_name=team_name, team_leader=team_leader).first()
        if duplicate_team:
            flash('A team with the same name and leader already exists.', 'team-error')
            return render_template('assign_team.html', tasks=tasks,ngos=ngos)

        # If no duplicate, create the new team
        new_team = Team(
            team_name=team_name,
            team_leader=team_leader,
            equipment=equipment,
            personnel=personnel,
            task_id=task_id,
            ngo_id=ngo_id
        )
        db.session.add(new_team)
        db.session.commit()
        flash('Team assigned successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('assign_team.html', tasks=tasks,ngos=ngos)

@app.route('/team_assignments')
@login_required

def team_assignments():
    events = EmergencyEvent.query.all()
    return render_template('team_assignments.html', events=events)

@app.route('/add_evacuation', methods=['GET', 'POST'])
@login_required
@admin_required
def add_evacuation():
    if request.method == 'POST':
        transport = request.form['transport']
        location = request.form['location']
        destination = request.form['destination']
        team_id = request.form['team_id']
        event_id = request.form['event_id']

        event = EmergencyEvent.query.get(event_id)

        evacuation = Evacuation(
            transport=transport,
            location=location,
            destination=destination,
            team_id=team_id,
            event_id=event_id,
            
        )
        db.session.add(evacuation)
        db.session.commit()
        flash('Evacuation assignment created successfully.')
        return redirect(url_for('dashboard'))

    teams = Team.query.all()
    events = EmergencyEvent.query.all()
    return render_template('add_evacuation.html', teams=teams, events=events)

@app.route('/view_evacuations')
@login_required

def view_evacuations():
    evacuations = Evacuation.query.all()
    return render_template('view_evacuations.html', evacuations=evacuations)

@app.route('/edit_evacuation/<int:evac_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_evacuation(evac_id):  # This must match the route parameter
    evacuation = Evacuation.query.get_or_404(evac_id)
    teams = Team.query.all()
    events = EmergencyEvent.query.all()

    if request.method == 'POST':
        evacuation.transport = request.form['transport']
        evacuation.location = request.form['location']
        evacuation.destination = request.form['destination']
        evacuation.team_id = request.form['team_id']
        evacuation.event_id = request.form['event_id']
        db.session.commit()
        flash('Evacuation updated successfully.')
        return redirect(url_for('view_evacuations'))

    return render_template('edit_evacuation.html', evacuation=evacuation, teams=teams, events=events)


@app.route('/delete_evacuation/<int:evac_id>', methods=['POST'])
@login_required
@admin_required
def delete_evacuation(evac_id):
    evacuation = Evacuation.query.get_or_404(evac_id)
    db.session.delete(evacuation)
    db.session.commit()
    flash('Evacuation deleted successfully.')
    return redirect(url_for('view_evacuations'))


@app.route('/add_ngo', methods=['GET', 'POST'])
@login_required
@admin_required
def add_ngo():
    if request.method == 'POST':
        name = request.form['name']
        contact_person = request.form['contact_person']
        contact_email = request.form['contact_email']
        phone = request.form['phone']
        address = request.form['address']

        # Check for duplicate NGO name
        existing = NGO.query.filter_by(name=name).first()
        if existing:
            flash('NGO with this name already exists.', 'error')
            return redirect(url_for('add_ngo'))

        new_ngo = NGO(
            name=name,
            contact_person=contact_person,
            contact_email=contact_email,
            phone=phone,
            address=address
        )
        db.session.add(new_ngo)
        db.session.commit()
        flash('NGO added successfully!', 'success')
        return redirect(url_for('add_ngo'))

    return render_template('add_ngo.html')

@app.route('/view_ngos', methods=['GET'])
@login_required
def view_ngos():
    ngos = NGO.query.all()
    return render_template('view_ngos.html', ngos=ngos)

@app.route('/delete_ngo/<int:ngo_id>', methods=['POST'])
@login_required
@admin_required
def delete_ngo(ngo_id):
    ngo = NGO.query.get_or_404(ngo_id)
    db.session.delete(ngo)
    db.session.commit()
    flash('NGO and all associated data deleted successfully.', 'success')
    return redirect(url_for('view_ngos'))

@app.route('/disaster-guide')
def disaster_guide():
    return render_template('disaster_guide.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")  # Flash message
    return render_template('home.html')   
     


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
