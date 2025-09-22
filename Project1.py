from Validations import PhoneValidationStrategy, ValidatorContext
from data import *
from person import *
from person_handling import FamilyFacade, RegistrationFacade, RoleManager, UserHandling
from postgres import PostgresSQl
from enums import BillOrganization, CharityOrganization, AppllicationDisplay, PaymentType, RequestType, Role
from mappers import *
from pay import *

def main():
    # Initialize components
    db_handler = PostgresSQl()
    registration = RegistrationFacade(db_handler)
    user_session = UserSession()
    
    while True:
        print(AppllicationDisplay.STARTING_APPLICATION.value)
        if user_session.get_user() is None:
            print(AppllicationDisplay.GET_USER_MESSAGE.value)            
            try:
                choice = input(AppllicationDisplay.SELECTING_OPTION.value).strip()
            except (EOFError, KeyboardInterrupt):
                print(AppllicationDisplay.INVALID_OPERATIION.value)
                              
            if choice == "1":
                # Registration use case
                print(AppllicationDisplay.Registration.value)
                try:
                    phone = input(AppllicationDisplay.PHONE_NUMBER.value).strip()
                    national_id = input(AppllicationDisplay.NATIONAL_ID.value).strip()
                    name = input(AppllicationDisplay.NAME.value).strip()
                    password = input(AppllicationDisplay.PASSWORD.value).strip()                
                    user = User(phone,national_id,name, password,Role.USER)       
                    result = registration.register_user(user)
                    print(result)
                except (EOFError, KeyboardInterrupt):
                    print(AppllicationDisplay.OPERATION_CANCELLED.value)
                    
            elif choice == "2":
                # Login use case
                print(AppllicationDisplay.LOGIN.value)
                try:
                    phone = input(AppllicationDisplay.PHONE_NUMBER.value).strip()
                    password = input(AppllicationDisplay.PASSWORD.value).strip()                
                    result = registration.login_user(phone, password)
                    print(result)                    
                except (EOFError, KeyboardInterrupt):
                    print(AppllicationDisplay.OPERATION_CANCELLED.value)                    
            elif choice == "3":
                print(AppllicationDisplay.CLOSING_APPLICATION.value)
                break
            else:
                print(AppllicationDisplay.INVALID_OPERATIION.value)
        else:
            current_user = user_session.get_user()
            print(f"Welcome, {current_user.name} ({current_user.role})!")
            print(AppllicationDisplay.MAIN_OPERATIONS_APPLIED.value)
            if current_user.role == Role.PARENT.value:
                print(AppllicationDisplay.PARENTOPERATIONS.value+"6. "+AppllicationDisplay.LOGOUT.value)
            else:
                print("5. "+AppllicationDisplay.LOGOUT.value)
            try:
                choice = input(AppllicationDisplay.SELECTING_OPTION.value).strip()
            except (EOFError, KeyboardInterrupt):
                print(AppllicationDisplay.INVALID_OPERATIION.value)
                continue
            if choice == "1":
                print(WalletRepresentation.display(current_user.wallet))
            elif choice == "2":
                print(AppllicationDisplay.MAKE_TRANSACTION.value)

                try:
                    tx_choice = input("Choose transaction type: ").strip()
                    amount = float(input("Amount: ").strip())

                    if tx_choice == "1":
                        # Send money use case
                        recipient_phone = input("Recipient phone number: ").strip()

                        # Validate recipient phone
                        phone_validator = ValidatorContext(PhoneValidationStrategy())
                        if not phone_validator.validate(recipient_phone):
                            print(f"❌ {phone_validator.get_error()}")
                            continue

                        # Check if recipient exists
                        recipient = QueryHandling.retrieve_data('User_',UserMapper,'','phone_number = %s',(recipient_phone,))
                        if recipient:
                            # Create transaction operation
                            tx_operation = TransactionOperation(current_user,recipient)
                            result = tx_operation.execute_transaction(PaymentType.SEND, amount)
                            print(result)
                        else:
                            print("Recipient not found")

                    elif tx_choice == "2":
                        # Receive money use case (simplified - usually triggered by sender)
                        # Check if recipient exists
                        # Send money use case
                        recipient_phone = input("Sender phone number: ").strip()

                        # Validate recipient phone
                        phone_validator = ValidatorContext(PhoneValidationStrategy())
                        if not phone_validator.validate(recipient_phone):
                            print(f"❌ {phone_validator.get_error()}")
                            continue
                        recipient = QueryHandling.retrieve_data('User_',UserMapper,'','phone_number = %s',(recipient_phone,))
                        if recipient:
                            # Create transaction operation
                            tx_operation = CollectMoney(current_user,amount,recipient)
                            result = tx_operation.execute(RequestType.COLLECT_MONEY)
                            print(result)
                        else:
                            print("Recipient not found")

                    elif tx_choice == "3":
                        # Donate to charity use case
                        print("Available charities:")
                        charities = list(CharityOrganization)
                        for i, charity in enumerate(charities, 1):
                            print(f"{i}. {charity.value}")

                        charity_choice = int(input("Choose charity: ").strip()) - 1
                        if 0 <= charity_choice < len(charities):
                            selected_charity = charities[charity_choice]
                            tx_operation = TransactionOperation(current_user,db_handler)
                            result = tx_operation.execute_transaction(PaymentType.DONATE, amount, selected_charity.value)
                            print(result)
                        else:
                            print("❌ Invalid charity selection")

                    elif tx_choice == "4":
                        # Pay bill use case
                        print("Available bill organizations:")
                        orgs = list(BillOrganization)
                        for i, org in enumerate(orgs, 1):
                            print(f"{i}. {org.value}")

                        org_choice = int(input("Choose organization: ").strip()) - 1
                        if 0 <= org_choice < len(orgs):
                            selected_org = orgs[org_choice]
                            tx_operation = TransactionOperation(current_user,db_handler)
                            result = tx_operation.execute_transaction(PaymentType.BILL_PAY, amount, selected_org.value)
                            print(result)
                        else:
                            print("❌ Invalid organization selection")

                    else:
                        print(AppllicationDisplay.INVALID_TRANSCTION.value)

                except (ValueError, EOFError, KeyboardInterrupt):
                    print(AppllicationDisplay.INVALID_OPERATIION.value)

            elif choice == "3":
                # View Transaction History use case
                print(UserHandling.get_user_transactions(current_user))

            elif choice == "4":
                # Change Role use case
                print(AppllicationDisplay.CHANGE_RULE_BLOCK.value)
                try:
                    role_choice = input(AppllicationDisplay.SELECTING_NEW_RULE.value).strip()
                    if role_choice == "1":
                        role = Role.USER
                    elif role_choice == "2":
                        role = Role.PARENT
                    else:
                        print("❌ Invalid role selection")
                        continue
                    result = RoleManager.change_user_role(current_user, role, db_handler)
                    print(result)

                except (EOFError, KeyboardInterrupt):
                    print(AppllicationDisplay.OPERATION_CANCELLED.value)
            elif choice == "5":
                if current_user.role == Role.PARENT.value:
                    # Family Wallet Operations use case (for parents only)
                    family_ops = FamilyFacade(user_session)
                    if not current_user.family_id:
                        print("No family wallet found. Creating one...")
                        fname = input("Enter family name: ").strip()
                        family_ops.create_family(fname)
                    print(AppllicationDisplay.FAMILY_BLOCK.value)
                    try:
                        family_choice = input("Choose option: ").strip()
                        if family_choice == "1":
                            # Add family member - enhanced to handle both existing and new users
                            print("\n--- Add Family Member ---")
                            # Add existing user
                            member_phone = input(AppllicationDisplay.PHONE_NUMBER.value).strip()
                            member_name = input(AppllicationDisplay.NAME.value).strip()
                            member_nid = input(AppllicationDisplay.NATIONAL_ID.value)
                            member_password = input(AppllicationDisplay.PASSWORD.value)
                            initial_limit = float(input(AppllicationDisplay.INITIAL_SPENDING_LIMIT.value).strip())
                            user = User(member_phone,member_nid,member_name, member_password,role=Role.CHILD)       
                            result = family_ops.create_child_account(user,maxlimit=initial_limit)
                            print(result)

                        elif family_choice == "2":
                            # View member info
                            member_phone = input(AppllicationDisplay.PHONE_NUMBER.value).strip()
                            info = family_ops.get_member_info(member_phone)
                            print(info)

                        elif family_choice == "3":
                            # Set spending limit
                            member_phone = input(AppllicationDisplay.PHONE_NUMBER.value).strip() 
                            new_limit = float(input("New max limit: ").strip())
                            result = family_ops.set_max_limit(member_phone, new_limit)
                            print(result)

                        elif family_choice == "4":
                            # View member transaction history
                            member_phone = input(AppllicationDisplay.PHONE_NUMBER.value).strip()
                            result = family_ops.see_transactions(member_phone)
                            print(result)

                        elif family_choice == "5":
                            # View all members transaction history
                            res = family_ops.see_all_children_history()
                            print(res)

                        elif family_choice == "6":
                            # List all members
                            members_list = family_ops.get_family_details()
                            print(members_list)
                        elif family_choice == "7":
                            # list all children 
                            children = family_ops.get_children_details()
                            print(children)                           
                        elif family_choice == "8":
                            # back to main menu
                            continue
                        else:
                            print("Invalid option")
                    except (ValueError, EOFError, KeyboardInterrupt):
                        print(AppllicationDisplay.INVALID_OPERATIION.value)
                else:
                    # Logout for non-parent users
                    user_session.clear_user()
                    print(AppllicationDisplay.LOGOUTMSG.value)        
            elif choice == "6" and current_user.role == Role.PARENT:
                # Logout use case for parents
                user_session.clear_user()
                print(AppllicationDisplay.LOGOUTMSG.value)

            else:
                print(AppllicationDisplay.INVALID_OPERATIION.value)
if __name__ == "__main__":
    main()