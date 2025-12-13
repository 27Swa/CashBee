from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
from users.models import User, Family, UsersRole
from wallet.models import Wallet, SystemLimit, PersonalLimit, FamilyLimit
from transactions.models import Transaction, CollectionRequest

class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Starting Data Population - 40+ Records Per Table'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # Ensure system limit exists
        self.stdout.write('\n⚙️  Checking System Limits...')
        self.ensure_system_limit()
        
        # Create families
        self.stdout.write('\n📋 Creating Families...')
        families = self.create_families()
        
        # Create users
        self.stdout.write('\n👥 Creating Users...')
        users = self.create_users(families)
        
        # Update wallet balances
        self.stdout.write('\n💰 Updating Wallet Balances...')
        self.update_wallet_balances(users)
        
        # Create family limits
        self.stdout.write('\n👨‍👩‍👧‍👦 Creating Family Limits...')
        self.create_family_limits(users)
        
        # Create personal limits
        self.stdout.write('\n📊 Creating Personal Limits...')
        self.create_personal_limits(users)
        
        # Create transactions
        self.stdout.write('\n💸 Creating Transactions...')
        transactions = self.create_transactions(users)
        
        # Create collection requests
        self.stdout.write('\n📬 Creating Collection Requests...')
        requests = self.create_collection_requests(users)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ Data Population Complete!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   Families: {Family.objects.count()}')
        self.stdout.write(f'   Users: {User.objects.count()}')
        self.stdout.write(f'   Wallets: {Wallet.objects.count()}')
        self.stdout.write(f'   System Limits: {SystemLimit.objects.count()}')
        self.stdout.write(f'   Family Limits: {FamilyLimit.objects.count()}')
        self.stdout.write(f'   Personal Limits: {PersonalLimit.objects.count()}')
        self.stdout.write(f'   Transactions: {Transaction.objects.count()}')
        self.stdout.write(f'   Collection Requests: {CollectionRequest.objects.count()}')
        self.stdout.write('\n')

    def ensure_system_limit(self):
        """Ensure system limit exists"""
        system_limit = SystemLimit.objects.filter(is_active=True).first()
        if not system_limit:
            system_limit = SystemLimit.objects.create(
                per_transaction_limit=Decimal('1000.00'),
                daily_limit=Decimal('5000.00'),
                monthly_limit=Decimal('20000.00'),
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Created system limit"))
        else:
            self.stdout.write(self.style.WARNING(f"System limit already exists"))

    def generate_valid_national_id(self, age, month=None, day=None):
        """Generate valid Egyptian National ID for specific age"""
        today = datetime.now()
        birth_year = today.year - age
        
        # Determine century digit
        if birth_year >= 2000:
            century_digit = '3'
            year_digits = str(birth_year - 2000).zfill(2)
        else:
            century_digit = '2'
            year_digits = str(birth_year - 1900).zfill(2)
        
        # Random or specified birth month/day
        birth_month = month or random.randint(1, 12)
        birth_day = day or random.randint(1, 28)
        
        month_str = str(birth_month).zfill(2)
        day_str = str(birth_day).zfill(2)
        
        # Governorate code (01-35)
        gov_code = str(random.randint(1, 35)).zfill(2)
        
        # Sequential number
        sequence = str(random.randint(1, 9999)).zfill(4)
        
        # Check digit
        check_digit = str(random.randint(0, 9))
        
        return century_digit + year_digits + month_str + day_str + gov_code + sequence + check_digit

    def create_families(self):
        """Create 10 family groups"""
        families_data = [
            "Hassan Family", "Ibrahim Family", "Ali Family", "Khalid Family", 
            "Samir Family", "Adel Family", "Nabil Family", "Fathy Family",
            "Hany Family", "Essam Family"
        ]
        
        families = []
        for name in families_data:
            family, created = Family.objects.get_or_create(name=name)
            families.append(family)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Created family: {name}"))
        
        return families

    def create_users(self, families):
        """Create 50+ users: admin + parents + children + regular users"""
        
        def build_user(first, last, phone, age, email, password, role, family=None):
            # Generate username from first and last name
            username = f"{first.lower()}.{last.lower()}"
            return {
                'username': username,
                'first_name': first,
                'last_name': last,
                'phone_number': phone,
                'national_id': self.generate_valid_national_id(age),
                'password': password,
                'role': role,
                'family': family,
                'email': email
            }

        users_data = []
        
        # ===== ADMIN/SUPERUSER =====
        admin_nid = self.generate_valid_national_id(35)
        try:
            admin = User.objects.get(is_superuser=True)
            self.stdout.write(self.style.WARNING(f"Admin already exists: {admin.name}"))
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                national_id=admin_nid,
                phone_number='01000000000',
                password='Admin@123456',
                first_name='Admin',
                last_name='User',
                email='admin@cashbee.com'
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Created ADMIN: {admin.name} - {admin.email}"))
        
        # ===== PARENTS (10 parents - age 30-55) =====
        parents_data = [
            ("Ahmed", "Hassan", "01012345678", 35, "ahmed.hassan@gmail.com"),
            ("Mohamed", "Ibrahim", "01123456789", 40, "mohamed.ibrahim@gmail.com"),
            ("Mahmoud", "Ali", "01234567890", 38, "mahmoud.ali@gmail.com"),
            ("Omar", "Khalid", "01098765432", 42, "omar.khalid@gmail.com"),
            ("Youssef", "Samir", "01187654321", 36, "youssef.samir@gmail.com"),
            ("Khaled", "Adel", "01276543210", 45, "khaled.adel@gmail.com"),
            ("Hassan", "Nabil", "01165432109", 38, "hassan.nabil@gmail.com"),
            ("Ibrahim", "Fathy", "01054321098", 41, "ibrahim.fathy@gmail.com"),
            ("Samir", "Hany", "01143210987", 37, "samir.hany@gmail.com"),
            ("Tarek", "Essam", "01232109876", 44, "tarek.essam@gmail.com"),
        ]
        for idx, (first, last, phone, age, email) in enumerate(parents_data):
            users_data.append(build_user(
                first, last, phone, age, email, 'Parent@123456', 
                UsersRole.PARENT, families[idx] if idx < len(families) else families[0]
            ))
     
        # ===== CHILDREN (15 children - age 8-17) =====
        children_data = [
            ("Sara", "Ahmed", "01011111111", 12, 0, "sara.ahmed@gmail.com"),
            ("Nour", "Mohamed", "01022222222", 15, 1, "nour.mohamed@gmail.com"),
            ("Adam", "Mahmoud", "01033333333", 10, 2, "adam.mahmoud@gmail.com"),
            ("Layla", "Omar", "01044444444", 14, 3, "layla.omar@gmail.com"),
            ("Ziad", "Youssef", "01055555555", 9, 4, "ziad.youssef@gmail.com"),
            ("Hana", "Ahmed", "01066666666", 17, 0, "hana.ahmed@gmail.com"),
            ("Yara", "Hassan", "01077777777", 11, 6, "yara.hassan@gmail.com"),
            ("Malak", "Ibrahim", "01088888888", 13, 7, "malak.ibrahim@gmail.com"),
            ("Karim", "Samir", "01099999999", 16, 8, "karim.samir@gmail.com"),
            ("Jana", "Tarek", "01010101010", 8, 9, "jana.tarek@gmail.com"),
            ("Farida", "Khaled", "01020202020", 15, 5, "farida.khaled@gmail.com"),
            ("Yousef", "Mahmoud", "01030303030", 12, 2, "yousef.mahmoud@gmail.com"),
            ("Nada", "Mohamed", "01040404040", 14, 1, "nada.mohamed@gmail.com"),
            ("Ali", "Omar", "01050505050", 10, 3, "ali.omar@gmail.com"),
            ("Maryam", "Youssef", "01060606060", 17, 4, "maryam.youssef@gmail.com"),
        ]
        for first, last, phone, age, family_idx, email in children_data:
            family = families[family_idx] if family_idx < len(families) else families[0]
            users_data.append(build_user(
                first, last, phone, age, email, 'Child@1234567', 
                UsersRole.CHILD, family
            ))
        
        # ===== REGULAR USERS (30 users - age 18-60) =====
        regular_users = [
            ("Kareem", "Essam", "01156789012", 25, "kareem.essam@gmail.com"),
            ("Mona", "Salem", "01267890123", 30, "mona.salem@gmail.com"),
            ("Tarek", "Fathy", "01023456789", 28, "tarek.fathy@gmail.com"),
            ("Dina", "Nabil", "01145678901", 22, "dina.nabil@gmail.com"),
            ("Hossam", "Ragab", "01289012345", 45, "hossam.ragab@gmail.com"),
            ("Salma", "Mostafa", "01034567890", 27, "salma.mostafa@gmail.com"),
            ("Amr", "Gamal", "01178901234", 33, "amr.gamal@gmail.com"),
            ("Rana", "Sherif", "01290123456", 24, "rana.sherif@gmail.com"),
            ("Hoda", "Adel", "01045678912", 29, "hoda.adel@gmail.com"),
            ("Waleed", "Sayed", "01156123456", 31, "waleed.sayed@gmail.com"),
            ("Noha", "Fahmy", "01267234567", 26, "noha.fahmy@gmail.com"),
            ("Khaled", "Aziz", "01078345678", 35, "khaled.aziz@gmail.com"),
            ("Yasmin", "Tamer", "01189456789", 23, "yasmin.tamer@gmail.com"),
            ("Sherif", "Medhat", "01290567890", 38, "sherif.medhat@gmail.com"),
            ("Aya", "Hany", "01001678901", 21, "aya.hany@gmail.com"),
            ("Ramy", "Fouad", "01112233445", 34, "ramy.fouad@gmail.com"),
            ("Nada", "Kamal", "01223344556", 29, "nada.kamal@gmail.com"),
            ("Basel", "Ashraf", "01034455667", 26, "basel.ashraf@gmail.com"),
            ("Mariam", "Sami", "01145566778", 32, "mariam.sami@gmail.com"),
            ("Omar", "Lotfy", "01256677889", 28, "omar.lotfy@gmail.com"),
            ("Farah", "Reda", "01067788990", 24, "farah.reda@gmail.com"),
            ("Adel", "Hamdy", "01178899001", 41, "adel.hamdy@gmail.com"),
            ("Shaimaa", "Magdy", "01289900112", 27, "shaimaa.magdy@gmail.com"),
            ("Mostafa", "Wael", "01090011223", 35, "mostafa.wael@gmail.com"),
            ("Eman", "Tarek", "01101122334", 30, "eman.tarek@gmail.com"),
            ("Tamer", "Yasser", "01212233445", 39, "tamer.yasser@gmail.com"),
            ("Heba", "Osama", "01023344556", 26, "heba.osama@gmail.com"),
            ("Samy", "Magdi", "01134455667", 31, "samy.magdi@gmail.com"),
            ("Nour", "Hesham", "01245566778", 23, "nour.hesham@gmail.com"),
            ("Hazem", "Ayman", "01056677889", 37, "hazem.ayman@gmail.com"),
        ]
        for first, last, phone, age, email in regular_users:
            users_data.append(build_user(
                first, last, phone, age, email, 'User@12345678', UsersRole.USER
            ))
     
        # Create all users
        created_users = []
        for user_data in users_data:
            # Try to get or create user by national_id
            try:
                user = User.objects.get(national_id=user_data['national_id'])
                created = False
                self.stdout.write(self.style.WARNING(f"User already exists: {user.name}"))
            except User.DoesNotExist:
                # Check if username exists and make it unique if needed
                base_username = user_data['username']
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user_data['username'] = username
                
                # Create new user
                user = User(**user_data)
                user.set_password(user_data['password'])
                user.save(skip_validation=True)  # Skip validation to avoid issues
                created = True
                self.stdout.write(self.style.SUCCESS(f"✓ Created user: {user.name} ({user.role})"))
            
            created_users.append(user)
        
        return created_users

    def update_wallet_balances(self, users):
        """Set realistic wallet balances"""
        for user in users:
            wallet = user.wallet
            if user.role == UsersRole.PARENT:
                wallet.balance = Decimal(random.uniform(5000, 18000))
            elif user.role == UsersRole.CHILD:
                wallet.balance = Decimal(random.uniform(100, 1500))
            else:  # Regular user
                wallet.balance = Decimal(random.uniform(1000, 12000))
            
            wallet.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Wallet for {user.name}: {wallet.balance:.2f} EGP"))

    def create_family_limits(self, users):
        """Create family limits for children"""
        parents = [u for u in users if u.role == UsersRole.PARENT]
        children = [u for u in users if u.role == UsersRole.CHILD]
        
        created_count = 0
        for child in children:
            # Find parent in same family
            parent = next((p for p in parents if p.family == child.family), None)
            if not parent:
                continue
            
            # Check if family limit already exists
            if FamilyLimit.objects.filter(parent=parent, child=child).exists():
                continue
            
            # Create family limit (more restrictive than system)
            family_limit = FamilyLimit.objects.create(
                parent=parent,
                child=child,
                per_transaction_limit=Decimal(random.uniform(50, 300)),
                daily_limit=Decimal(random.uniform(300, 800)),
                monthly_limit=Decimal(random.uniform(800, 2500)),
                is_active=True
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f"✓ Family limit: {parent.name} → {child.name} "
                f"(Tx: {family_limit.per_transaction_limit}, "
                f"Daily: {family_limit.daily_limit}, "
                f"Monthly: {family_limit.monthly_limit})"
            ))
        
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} family limits"))

    def create_personal_limits(self, users):
        """Create personal limits for some users"""
        # Create personal limits for 30% of regular users and 50% of children
        regular_users = [u for u in users if u.role == UsersRole.USER]
        children = [u for u in users if u.role == UsersRole.CHILD]
        
        created_count = 0
        
        # Personal limits for regular users (30%)
        for user in random.sample(regular_users, k=int(len(regular_users) * 0.3)):
            if PersonalLimit.objects.filter(user=user).exists():
                continue
            
            personal_limit = PersonalLimit.objects.create(
                user=user,
                per_transaction_limit=Decimal(random.uniform(200, 800)),
                daily_limit=Decimal(random.uniform(800, 3000)),
                monthly_limit=Decimal(random.uniform(3000, 15000)),
                is_active=True
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f"✓ Personal limit for {user.name}: "
                f"Tx: {personal_limit.per_transaction_limit}, "
                f"Daily: {personal_limit.daily_limit}, "
                f"Monthly: {personal_limit.monthly_limit}"
            ))
        
        # Personal limits for children (50%)
        for child in random.sample(children, k=int(len(children) * 0.5)):
            if PersonalLimit.objects.filter(user=child).exists():
                continue
            
            # Get their family limit to ensure personal is more restrictive
            try:
                family_limit = FamilyLimit.objects.get(child=child, is_active=True)
                
                personal_limit = PersonalLimit.objects.create(
                    user=child,
                    per_transaction_limit=Decimal(min(
                        float(family_limit.per_transaction_limit) * 0.7,
                        random.uniform(20, 100)
                    )),
                    daily_limit=Decimal(min(
                        float(family_limit.daily_limit) * 0.7,
                        random.uniform(100, 400)
                    )),
                    monthly_limit=Decimal(min(
                        float(family_limit.monthly_limit) * 0.7,
                        random.uniform(400, 1500)
                    )),
                    is_active=True
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Personal limit for {child.name}: "
                    f"Tx: {personal_limit.per_transaction_limit}, "
                    f"Daily: {personal_limit.daily_limit}, "
                    f"Monthly: {personal_limit.monthly_limit}"
                ))
            except FamilyLimit.DoesNotExist:
                continue
        
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} personal limits"))

    def create_transactions(self, users):
        """Create transactions between users"""
        def create_tx(sender, receiver, amount, status, max_days_ago):
            """Helper to create and log a transaction."""
            tx = Transaction.objects.create(
                from_wallet=sender.wallet,
                to_wallet=receiver.wallet,
                amount=round(amount, 2),
                transaction_type=Transaction.TransactionType.SEND,
                status=status,
                from_wallet_balance_before=sender.wallet.balance,
                to_wallet_balance_before=receiver.wallet.balance
            )
            # Randomize transaction date
            days_ago = random.randint(0, max_days_ago)
            tx.date = timezone.now() - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            tx.save(update_fields=['date'])
            transactions.append(tx)
            self.stdout.write(
                self.style.SUCCESS(f"✓ TX: {sender.name} → {receiver.name}: {amount:.2f} EGP ({status})")
            )

        transactions = []
        
        # Get users by role
        parents = [u for u in users if u.role == UsersRole.PARENT]
        children = [u for u in users if u.role == UsersRole.CHILD]
        regular = [u for u in users if u.role == UsersRole.USER]
        
        # Parent → Child Transactions (15)
        for _ in range(15):
            parent = random.choice(parents)
            family_children = [c for c in children if c.family == parent.family]
            if not family_children:
                continue

            child = random.choice(family_children)
            amount = Decimal(random.uniform(50, 500))

            if parent.wallet.balance >= amount:
                create_tx(parent, child, amount, Transaction.TransactionStatus.SUCCESS, max_days_ago=30)

        # Regular → Regular Transactions (35)
        for _ in range(35):
            sender = random.choice(regular)
            receiver = random.choice([u for u in regular if u != sender])
            amount = Decimal(random.uniform(100, 2000))

            if sender.wallet.balance < amount:
                continue

            # Randomize transaction status
            rand = random.random()
            if rand < 0.75:
                status = Transaction.TransactionStatus.SUCCESS
            elif rand < 0.95:
                status = Transaction.TransactionStatus.FAILED
            else:
                status = Transaction.TransactionStatus.PENDING

            create_tx(sender, receiver, amount, status, max_days_ago=60)

        return transactions

    def create_collection_requests(self, users):
        """Create 50+ collection requests with validation"""
        def create_request(from_user, to_user, status, note=None):
            amount = Decimal(random.uniform(100, 1500))
            created_days_ago = random.randint(1, 45)
            created_at = timezone.now() - timedelta(days=created_days_ago, hours=random.randint(0, 23))

            req = CollectionRequest.objects.create(
                from_user=from_user,
                to_user=to_user,
                amount=round(amount, 2),
                status=status,
                req_type=CollectionRequest.ReqType.COLLECT_MONEY,
                note=note or f"Request from {from_user.name} to {to_user.name}"
            )

            req.created_at = created_at
            req.save(update_fields=['created_at'])
            requests.append(req)

            self.stdout.write(self.style.SUCCESS(
                f"✓ Request ({status}): {from_user.name} → {to_user.name} : {amount:.2f} EGP"
            ))

        requests = []
    
        regular = [u for u in users if u.role == UsersRole.USER]
        parents = [u for u in users if u.role == UsersRole.PARENT]
        children = [u for u in users if u.role == UsersRole.CHILD]
            
        child_notes = [
            "Allowance request for this week",
            "Need money for school trip",
            "Request for new school supplies",
            "Lunch money for the week",
            "Need funds for an activity"
        ]
        
        # Child → Parent (12)
        for child in children:
            parent = next((p for p in parents if p.family == child.family), None)
            if parent:
                status = random.choices(
                    [CollectionRequest.Status.PENDING, CollectionRequest.Status.APPROVED, CollectionRequest.Status.REJECTED],
                    [0.6, 0.3, 0.1]
                )[0]
                create_request(child, parent, status, random.choice(child_notes))
        
        # Parent ↔ Parent / Parent ↔ User
        parent_notes = [
            "Family expense sharing",
            "Group activity payment",
            "Helping another user with expenses",
            "Payback for last outing"
        ]
        for parent in parents:
            possible_targets = [u for u in parents + regular if u != parent]
            to_user = random.choice(possible_targets)
            status = random.choices(
                [CollectionRequest.Status.PENDING, CollectionRequest.Status.APPROVED, CollectionRequest.Status.REJECTED],
                [0.4, 0.4, 0.2]
            )[0]
            create_request(parent, to_user, status, random.choice(parent_notes))

        # User ↔ User / User ↔ Parent
        user_notes = [
            "Splitting restaurant bill",
            "Contributing to shared expense",
            "Payback for previous purchase",
            "Requesting help from parent",
            "Shared project contribution"
        ]
        for user in regular:
            if random.random() < 0.5:
                to_user = random.choice([u for u in regular if u != user])
            else:
                to_user = random.choice(parents)
            status = random.choices(
                [CollectionRequest.Status.PENDING, CollectionRequest.Status.APPROVED, CollectionRequest.Status.REJECTED],
                [0.5, 0.3, 0.2]
            )[0]
            create_request(user, to_user, status, random.choice(user_notes))

        return requests