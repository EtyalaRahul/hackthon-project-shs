"""
Generate 5000 sample leads for testing batch processing
"""

import csv
import random

# Sample data pools
first_names = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna"
]

last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy"
]

company_types = [
    "Corp", "Inc", "Solutions", "Technologies", "Systems", "Group", "Enterprises",
    "Industries", "Services", "Partners", "Labs", "Dynamics", "Innovations", "Holdings",
    "Digital", "Global", "Networks", "Ventures", "Capital", "Consulting"
]

company_prefixes = [
    "Tech", "Data", "Cloud", "Smart", "Global", "Mega", "Alpha", "Beta", "Quantum",
    "Cyber", "Digital", "Future", "Prime", "Elite", "Advanced", "Strategic", "Dynamic",
    "Innovative", "Enterprise", "Professional", "Modern", "Integrated", "Unified", "Optimal"
]

company_sizes = ["1-10", "10-50", "50-200", "200-500", "500-1000", "1000+"]

# High-value roles (executives and decision makers)
high_value_roles = [
    "CEO", "CTO", "CFO", "COO", "VP of Sales", "VP of Engineering", "VP of Operations",
    "Chief Revenue Officer", "Chief Technology Officer", "Chief Information Officer",
    "Director of Sales", "Director of IT", "Director of Operations", "Head of Engineering",
    "Head of Product", "Sales Director", "IT Director", "Operations Director"
]

# Medium-value roles
medium_value_roles = [
    "Senior Manager", "Product Manager", "Engineering Manager", "Sales Manager",
    "IT Manager", "Operations Manager", "Marketing Manager", "Project Manager",
    "Team Lead", "Senior Developer", "Lead Engineer", "Account Manager",
    "Business Analyst", "Solutions Architect", "Technical Lead"
]

# Low-value roles
low_value_roles = [
    "Student", "Intern", "Professor", "Teacher", "Freelancer", "Job Seeker",
    "Volunteer", "Researcher", "Consultant", "Contractor"
]

# High-priority message templates (urgent, budget, authority)
high_priority_messages = [
    "Urgent migration needed from Salesforce. Budget approved for {size}+ users. Need to start immediately.",
    "Critical deadline approaching. Current system failing. Budget of ${budget}K allocated. Enterprise plan needed.",
    "Emergency! Our vendor is going bankrupt. Need replacement ASAP for {size} employees. Contract ready.",
    "Urgent: System migration required by end of Q{quarter}. {size}+ users. Budget approved and allocated.",
    "Time-sensitive opportunity. Board approved ${budget}K budget. Need enterprise solution for {size}+ team.",
    "Critical business need. Current CRM failing. Budget in place. Need to onboard {size} sales reps immediately.",
    "Urgent enterprise migration. {size}+ users across {regions} regions. Contract ready to sign.",
    "Immediate need for {size}-user deployment. Budget approved. Deadline in {weeks} weeks.",
    "Crisis situation! Current platform unstable. ${budget}K budget allocated. Need solution for {size}+ staff.",
    "Urgent RFP response needed. Enterprise deployment for {size} users. Budget confirmed."
]

# Medium-priority message templates (interested, demo, evaluation)
medium_priority_messages = [
    "Interested in learning more about your CRM solution for our {size}-person team.",
    "Would like to schedule a demo to see if this fits our needs. Company size: {size} employees.",
    "Looking to evaluate CRM options for our growing business. Currently have {size} staff.",
    "Considering switching from our current solution. Can you provide pricing for {size} users?",
    "Want to explore your platform features. We're a {size}-person company in growth mode.",
    "Interested in a trial. Our team of {size} is evaluating several CRM platforms.",
    "Could you share more information about enterprise features? We have {size} employees.",
    "Looking for a CRM solution. Team size is around {size}. What's your pricing?",
    "Evaluating different platforms. Would appreciate a call to discuss our needs. Team: {size} people.",
    "Interested in your product. Can someone contact me to discuss options for {size} users?"
]

# Low-priority message templates (students, job seekers, poor fit)
low_priority_messages = [
    "I'm a student working on a thesis project. Can I get free access?",
    "Are you hiring? I'm looking for a sales position.",
    "Do you offer educational discounts for universities?",
    "Just browsing. Thanks!",
    "Can students use this for school projects?",
    "I'm doing research on CRM systems for my dissertation.",
    "Looking for internship opportunities in your company.",
    "Are there any volunteer positions available?",
    "Is this free for personal use?",
    "What's your hiring process like?"
]

# Spam message templates
spam_messages = [
    "Make $10000 a month working from home!!! Click here now!!!",
    "URGENT: You've won a prize! Claim now by visiting our website!",
    "Earn money fast! No experience needed! Start today!!!",
    "GET RICH QUICK! Limited time offer! Act now!!!",
    "FREE MONEY! Click here to claim your reward!!!",
    "Work from home and earn $$$$! Sign up today!",
    "SPECIAL OFFER! Buy now and get 90% off!!!",
    "You've been selected for a special promotion! Click now!",
    "Make millions online! No investment required!",
    "CONGRATULATIONS! You're a winner! Claim your prize!"
]

def generate_lead(lead_id):
    """Generate a single lead record"""
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    # Determine lead quality (30% high, 45% medium, 20% low, 5% spam)
    quality = random.random()
    
    if quality < 0.30:  # High priority (30%)
        role = random.choice(high_value_roles)
        company_size = random.choice(["200-500", "500-1000", "1000+"])
        message_template = random.choice(high_priority_messages)
        
        # Fill in variables
        message = message_template.format(
            size=random.choice([100, 200, 300, 500, 800, 1000, 1200, 1500]),
            budget=random.choice([50, 100, 150, 200, 250, 500, 750, 1000]),
            quarter=random.choice([1, 2, 3, 4]),
            regions=random.choice([2, 3, 4, 5, 6, 8, 10]),
            weeks=random.choice([2, 3, 4, 6, 8])
        )
        
    elif quality < 0.75:  # Medium priority (45%)
        role = random.choice(medium_value_roles)
        company_size = random.choice(["10-50", "50-200", "200-500"])
        message_template = random.choice(medium_priority_messages)
        message = message_template.format(
            size=random.choice([15, 25, 50, 75, 100, 150, 200])
        )
        
    elif quality < 0.95:  # Low priority (20%)
        role = random.choice(low_value_roles)
        company_size = random.choice(["1-10", "10-50"])
        message = random.choice(low_priority_messages)
        
    else:  # Spam (5%)
        role = random.choice(["Promoter", "Marketer", "Spammer", "Agent", "Representative"])
        company_size = "1-10"
        message = random.choice(spam_messages)
    
    # Generate email and company
    email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(['company', 'corp', 'business', 'tech', 'email', 'mail'])}.com"
    company_name = f"{random.choice(company_prefixes)} {random.choice(company_types)}"
    
    return {
        "lead_id": lead_id,
        "full_name": f"{first_name} {last_name}",
        "email": email,
        "company_name": company_name,
        "company_size": company_size,
        "role": role,
        "message": message
    }

def generate_leads_csv(filename, count=5000):
    """Generate CSV file with specified number of leads"""
    print(f"Generating {count} leads...")
    
    fieldnames = ["lead_id", "full_name", "email", "company_name", "company_size", "role", "message"]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(1, count + 1):
            lead = generate_lead(i)
            writer.writerow(lead)
            
            if i % 500 == 0:
                print(f"  Generated {i}/{count} leads...")
    
    print(f"✅ Successfully generated {count} leads in {filename}")

if __name__ == "__main__":
    generate_leads_csv("lead_data.csv", 5000)
