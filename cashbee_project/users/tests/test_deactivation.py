"""
Test script to diagnose user deactivation issues
Run with: python manage.py shell < test_deactivation.py
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.core.exceptions import ValidationError

User = get_user_model()

print("\n" + "="*60)
print("🔍 TESTING USER DEACTIVATION")
print("="*60 + "\n")

# Test 1: Check if User model has required fields
print("TEST 1: Checking User model structure...")
try:
    user_fields = [f.name for f in User._meta.get_fields()]
    print("✅ User model fields:", user_fields)
    
    if 'is_active' in user_fields:
        print("✅ is_active field exists")
    else:
        print("❌ is_active field missing!")
        
except Exception as e:
    print(f"❌ Error checking model: {e}")

print("\n" + "-"*60 + "\n")

# Test 2: Check if name property exists
print("TEST 2: Checking name property...")
try:
    test_user = User.objects.filter(is_active=True).first()
    if test_user:
        print(f"✅ Test user found: {test_user.username}")
        try:
            name = test_user.name
            print(f"✅ name property works: '{name}'")
        except AttributeError:
            print("❌ name property doesn't exist!")
            print("   Add this to your User model:")
            print("""
    @property
    def name(self):
        return self.get_full_name() or self.first_name or self.username
            """)
    else:
        print("⚠️  No active users found to test")
except Exception as e:
    print(f"❌ Error testing name property: {e}")

print("\n" + "-"*60 + "\n")

# Test 3: Check wallet relationship
print("TEST 3: Checking wallet relationship...")
try:
    users_with_wallet = 0
    users_without_wallet = 0
    
    for user in User.objects.all()[:5]:
        try:
            wallet = user.wallet
            users_with_wallet += 1
            print(f"✅ {user.username} has wallet (ID: {wallet.id})")
        except:
            users_without_wallet += 1
            print(f"⚠️  {user.username} has NO wallet")
    
    if users_without_wallet > 0:
        print(f"\n❌ {users_without_wallet} users don't have wallets!")
        print("   This might cause serializer errors")
        
except Exception as e:
    print(f"❌ Error checking wallets: {e}")

print("\n" + "-"*60 + "\n")

# Test 4: Test direct database update
print("TEST 4: Testing direct database update...")
try:
    # Find a user to test (not superuser)
    test_user = User.objects.filter(
        is_active=True,
        is_superuser=False
    ).first()
    
    if test_user:
        original_status = test_user.is_active
        print(f"📝 Testing with user: {test_user.username}")
        print(f"   Original status: is_active={original_status}")
        
        # Try to update
        affected = User.objects.filter(pk=test_user.pk).update(is_active=False)
        print(f"✅ Update query affected {affected} row(s)")
        
        # Verify
        test_user.refresh_from_db()
        print(f"   New status: is_active={test_user.is_active}")
        
        # Restore original status
        User.objects.filter(pk=test_user.pk).update(is_active=original_status)
        test_user.refresh_from_db()
        print(f"✅ Restored to: is_active={test_user.is_active}")
    else:
        print("⚠️  No suitable test user found")
        
except Exception as e:
    print(f"❌ Error in direct update test: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-"*60 + "\n")

# Test 5: Check for signals that might interfere
print("TEST 5: Checking for signals...")
try:
    from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
    
    signals_to_check = [
        (pre_save, "pre_save"),
        (post_save, "post_save"),
        (pre_delete, "pre_delete"),
        (post_delete, "post_delete"),
    ]
    
    for signal, signal_name in signals_to_check:
        receivers = signal.receivers
        user_receivers = [
            r for r in receivers 
            if r[0][0] == User or (hasattr(r[0][0], '__name__') and 'User' in r[0][0].__name__)
        ]
        
        if user_receivers:
            print(f"⚠️  Found {len(user_receivers)} {signal_name} receivers for User")
        else:
            print(f"✅ No {signal_name} receivers for User")
            
except Exception as e:
    print(f"⚠️  Could not check signals: {e}")

print("\n" + "="*60)
print("🏁 DIAGNOSIS COMPLETE")
print("="*60 + "\n")

print("📋 SUMMARY:")
print("1. Check the results above for ❌ errors")
print("2. Most common issues:")
print("   - Missing 'name' property in User model")
print("   - Users without wallets causing serializer errors")
print("   - Signals interfering with updates")
print("\n3. If direct update works but API doesn't:")
print("   - Check your destroy() method in views.py")
print("   - Verify permissions are correct")
print("   - Check serializer read_only_fields")
print("\n4. Check Django logs for the actual 500 error traceback")
print("\n")