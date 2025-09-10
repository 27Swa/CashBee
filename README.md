# CashBee

## Overview
CashBee is an all-in-one mobile wallet for seamless money transfers, bill payments, and donations. Its unique family feature allows the main user to create and manage limited-access sub-accounts for children, providing security and financial control.


## Scope
| Feature | Description |
|---------|-------------|
| **User Authentication** | Register / Login |
| **Transaction Management** | Set transaction limits |
| **Pay** | Send money |
| **Bill Payment** | Pay bills (Gas, Water, Electricity) |
| **Donation** | Send money to charitable organizations  |
| **Money Collection** | Collect money from others |
| **Transaction History** | View payment and collection history |
| **Family Wallet** | Manage family wallet accounts |

## Architecture
It is designed using a layered architecture to ensure scalability, security, and ease of maintenance.  
1. **Frontend (Mobile Application):** Flutter  
2. **Backend (Server Layer):** Django (Python)  
3. **Database Layer**: PostgreSQL  
4. **Authentication & Security:** Django Authentication + JWT  
5. **Notifications Service:** Firebase Cloud Messaging (FCM)  

```mermaid
flowchart TD
    subgraph Frontend[Flutter Mobile App]
        Screens[App Screens]
        Logic[App Logic]
    end

    subgraph Backend[Django Server]
        API[API Layer]
        Services[Backend Services]
        Auth[Authentication Service]
        FCM_Handler[FCM Handler]
    end

    subgraph Database[PostgreSQL Database]
        Tables[Data Storage]
    end

    %% User Interaction
    User[User] -->|Interacts with| Screens

    %% App Internal Flow
    Screens <-->|Manages UI & Data| Logic

    %% Communication with Backend
    Logic -->|Sends Requests| API
    API -->|Sends Responses| Logic

    %% Backend Internal Flow
    API -->|Uses| Services
    Services -->|Reads/Writes Data| Tables
    API -->|Validates User| Auth
    API -->|Prepares Notification| FCM_Handler

    %% Notification Flow
    FCM_Handler -->|Sends Push Notification| Screens

```
## Process
 How the Family Wallet Application Works:
1. **User Registration & Authentication**
   - Parents/Guardians register and create a main account
   - Children get sub-accounts with parental-controlled access
   - Role-based permissions determine what each user can access
```mermaid
flowchart TD
    A[Parent Registers/Logs In] --> B[Parent Dashboard]
    B --> C[Add Family Member]
    C --> E[Child Account Created]
    E --> G[Child Logs In]
```

2. **Transaction Limits Configuration**
   - Parents set spending limits for each child individually
   - Establish family-wide transaction limits
   - Customize limits by transaction type (payments, donations, etc.)
```mermaid
flowchart TD
    Start[Limit Configuration] --> SelectUser[Select Family Member]
    SelectUser --> CheckRole{User Role?}
    
    %% Parent Flow
    CheckRole -->|Parent/Guardian| ParentChoice{Set Own Transaction Limit?}
    
    ParentChoice -->|Yes| SetParentLimit[Set Parent Transaction Limit]
    ParentChoice -->|No| SkipParent[Skip Setting Parent Limit]
    
    SetParentLimit --> CheckChildren{Are Children Registered?}
    SkipParent --> CheckChildren
    
    CheckChildren -->|Yes| SetChildrenLimits[Set Limits for Children]
    CheckChildren -->|No| CheckAnyLimit{Any Limits Set?}
    
    SetChildrenLimits --> CheckAnyLimit
    
    CheckAnyLimit -->|Yes| SaveLimits[Save Limit Settings]
    CheckAnyLimit -->|No| ShowExisting[Show Existing Limits]
    
    SaveLimits --> Confirm[Confirm Configuration]
    Confirm --> Apply["Apply to Selected User(s)"]
    Apply --> End[Limits Activated]
    
    ShowExisting --> End
    
    %% Child Flow (for direct child login if needed)
    CheckRole -->|Child| SetIndividual[View/Use Assigned Limits]
    SetIndividual --> End
```

3. **Financial Operations**
   - Direct Payments: Send money to contacts via QR code or phone number
   - Bill Payments: Utilities (electricity, water, gas) payment facility
   - Donations: Support approved charitable organizations
   - Money Collection: Request and receive funds from family members or contacts
    ```mermaid
    flowchart TD
    Start[Financial Operations] --> ChooseType[Choose Transaction Type]
    
    ChooseType --> Payment[Direct Payment]
    ChooseType --> BillPay[Bill Payment]
    ChooseType --> Donation[Donation]
    ChooseType --> MoneyCollect[Money Collection]
    
    Payment --> EnterDetails[Enter Payment Details]
    BillPay --> SelectBiller[Select Biller Company]
    Donation --> ChooseCharity[Choose Charity]
    MoneyCollect --> CreateRequest[Create Collection Request]
    
    EnterDetails --> ConfirmPayment[Confirm Payment]
    SelectBiller --> ConfirmBill[Confirm Bill Payment]
    ChooseCharity --> ConfirmDonation[Confirm Donation]
    CreateRequest --> SendRequest[Send Request]
    
    ConfirmPayment --> ProcessPayment[Process Transaction]
    ConfirmBill --> ProcessPayment
    ConfirmDonation --> ProcessPayment
    SendRequest --> WaitResponse[Wait for Response]
    
    ProcessPayment --> UpdateHistory[Update Transaction History]
    WaitResponse --> UpdateHistory
    
    UpdateHistory --> Notify[Send Notification]
    Notify --> ReturnHome[Return to Home]
    ```

4. **Transaction Monitoring & History**
   - All transactions are logged with detailed information
   - Filterable view by: child, date, transaction type, or amount
   - Real-time notifications for all financial activities
```mermaid
flowchart TD
    A[User Selects 'History'] --> B{User Type?}
    B -- Parent --> C[View All Family Transactions]
    B -- Child --> D[View Own Transactions Only]
    C --> E[Filter by: Child, Date, Type]
    D --> F[Filter by: Date, Type]
    E --> G[Display Results]
    F --> G
    G --> H[Return to Home]
```
5. **Family Management**
   - Parents can add/remove family members
   - Customizable permissions for each family member
   - Centralized oversight of all family financial activities
```mermaid
flowchart TD
    Start[Family Management] --> AccessDashboard[Access Parent Dashboard]
    AccessDashboard --> ChooseAction[Choose Management Action]
    
    ChooseAction --> AddMember[Add Family Member]
    ChooseAction --> RemoveMember[Remove Family Member]
    ChooseAction --> ModifyPermissions[Modify Permissions]
    
    AddMember --> EnterDetails[Enter Member Details]
    EnterDetails --> SetInitialPerms[Set Initial Permissions]
    SetInitialPerms --> ConfirmAdd[Confirm Addition]
    
    RemoveMember --> SelectMember[Select Member to Remove]
    SelectMember --> ConfirmRemove[Confirm Removal]
    
    ModifyPermissions --> ChooseMember[Choose Family Member]
    ChooseMember --> AdjustPermissions[Adjust Permission Settings]
    AdjustPermissions --> SaveChanges[Save Changes]
    
    ConfirmAdd --> UpdateSystem[Update System Records]
    ConfirmRemove --> UpdateSystem
    SaveChanges --> UpdateSystem
    
    UpdateSystem --> SendNotification[Send Notification to Affected Users]
    SendNotification --> ReturnDash[Return to Dashboard]
```
# Class Diagram
1. Core Domain Models
   This section shows the fundamental business entities of the system.
```mermaid
classDiagram
    %% ========== Validation Check ==========
    class ValidationCheck {
        - validation_checks: list
        + __init__(name, phone, password, national_id)
        + check() str
    }
    
    class ValidationsNames {
        <<Enum>>
        NAME
        PHONE
        PASSWORD
        NATIONALID
    }
    
    ValidationCheck --> ValidationsNames : uses
    ValidationCheck --> ValidatorContext : uses
    
    %% ========== Strategy Pattern ==========
    class ValidatorContext {
        - _strategy: ValidationStrategy
        + __init__(strategy: ValidationStrategy)
        + set_strategy(strategy: ValidationStrategy)
        + validate(value) bool
        + get_error() str
    }
    
    class ValidationStrategy {
        <<interface>>
        + is_valid(value) bool
        + get_error_message() str
    }
    
    class NationalIDValidationStrategy {
        + is_valid(value) bool
        + get_error_message() str
    }
    
    class ChildNationalIDValidationStrategy {
        + is_valid(value) bool
        + get_error_message() str
    }
    
    class PhoneValidationStrategy {
        + is_valid(value) bool
        + get_error_message() str
    }
    
    class PasswordValidationStrategy {
        + is_valid(value) bool
        + get_error_message() str
    }
    
    class EnglishNameValidationStrategy {
        + is_valid(value) bool
        + get_error_message() str
    }
    
    class RegexPattern {
        <<Enum>>
        LOWERCASE_ENGLISH
        UPPERCASE_ENGLISH
        NUMBERS
        SPECIAL_CHARACTERS
    }
    
    ValidatorContext --> ValidationStrategy : has
    ValidationStrategy <|.. NationalIDValidationStrategy : implements
    ValidationStrategy <|.. ChildNationalIDValidationStrategy : implements
    ValidationStrategy <|.. PhoneValidationStrategy : implements
    ValidationStrategy <|.. PasswordValidationStrategy : implements
    ValidationStrategy <|.. EnglishNameValidationStrategy : implements
    PasswordValidationStrategy --> RegexPattern : uses
    EnglishNameValidationStrategy --> RegexPattern : uses
```
2.  Enumerations & Constants
   This section defines the system's enumerations and constant values.
```mermaid
classDiagram
    class Role {
        <<enumeration>>
        PARENT
        CHILD
        USER
    }
    
    class PaymentType {
        <<enumeration>>
        SEND
        RECEIVE
        DONATE
        BILL_PAY
    }
    
    class BillOrganization {
        <<enumeration>>
        GAS
        WATER
        ELECTRICITY
    }
    
    class CharityOrganization {
        <<enumeration>>
        MISR_EL_KHEIR
        RESALA
        FOOD_BANK
        MAGDI_YACOUB
        HOSPITAL_57357
        BAHEYA
        COPTIC_ORTHODOX
        RED_CRESCENT
    }
    
    class TransactionLimits {
        <<enumeration>>
        PER_OPERATION_LIMIT: 500
        DAILY_LIMIT: 1500
        WEEKLY_LIMIT: 10500
        MONTHLY_LIMIT: 315000
    }
    
    class RegexPattern {
        <<enumeration>>
        LOWERCASE_ENGLISH
        UPPERCASE_ENGLISH
        NUMBERS
        SPECIAL_CHARACTERS
    }
```
3. Validation System
```mermaid
classDiagram
    class ValidationStrategy {
        <<abstract>>
        +is_valid(value): bool*
        +get_error_message(): str*
    }
    
    class ValidatorContext {
        -_strategy: ValidationStrategy
        +__init__(strategy)
        +set_strategy(strategy): void
        +validate(value): bool
        +get_error(): str
    }
    
    class NationalIDValidationStrategy {
        +is_valid(nid): bool
        +get_error_message(): str
    }
    
    class ChildNationalIDValidationStrategy {
        +is_valid(nid): bool
        +get_error_message(): str
    }
    
    class PhoneValidationStrategy {
        +is_valid(value): bool
        +get_error_message(): str
    }
    
    class PasswordValidationStrategy {
        +is_valid(password): bool
        +get_error_message(): str
    }
    
    class EnglishNameValidationStrategy {
        +is_valid(val): bool
        +get_error_message(): str
    }
    
    class ValidationCheck {
        +validation_checks: List
        +__init__(name, phone, password, national_id)
        +check(): str
    }
    
    class ValidationsNames {
        <<enumeration>>
        NAME: ValidatorContext
        PHONE: ValidatorContext
        PASSWORD: ValidatorContext
        NATIONALID: ValidatorContext
    }
    
    ValidationStrategy <|-- NationalIDValidationStrategy
    ValidationStrategy <|-- ChildNationalIDValidationStrategy
    ValidationStrategy <|-- PhoneValidationStrategy
    ValidationStrategy <|-- PasswordValidationStrategy
    ValidationStrategy <|-- EnglishNameValidationStrategy
    ValidatorContext o-- ValidationStrategy
    ValidationCheck --> ValidationsNames
    ValidationsNames --> ValidatorContext
```
4.  Payment System
```mermaid
classDiagram
    class Payment {
        <<abstract>>
        +from_user_id: str
        +amount: float
        +to: str
        +tx_type: PaymentType
        +date: datetime
        +__init__(from_user_id, amount, to, tx_type)
        +execute(wallet): str*
        +_validate(wallet): str
        +_create_transaction(): Transaction
    }
    
    class SendPayment {
        +__init__(from_user_id, amount, to)
        +execute(wallet): str
    }
    
    class ReceivePayment {
        +__init__(from_user_id, amount, to)
        +execute(wallet): str
    }
    
    class DonationPayment {
        +__init__(from_user_id, amount, to)
        +execute(wallet): str
    }
    
    class BillPayment {
        +__init__(from_user_id, amount, to)
        +execute(wallet): str
    }
    
    class PaymentFactory {
        <<static>>
        +create_payment(payment_type, from_user_id, amount, to): Payment
    }
    
    Payment <|-- SendPayment
    Payment <|-- ReceivePayment
    Payment <|-- DonationPayment
    Payment <|-- BillPayment
    PaymentFactory ..> Payment : creates
    PaymentFactory --> PaymentType
```
5. Notification System
```mermaid
classDiagram
    class TransactionObserver {
        <<abstract>>
        +update(transaction): void*
    }
    
    class SMSNotificationObserver {
        +update(transaction): void
    }
    
    class TransactionSubject {
        -_observers: List[TransactionObserver]
        +attach(observer): void
        +detach(observer): void
        +notify(transaction): void
    }
    
    class TransactionOperation {
        +user1: User
        +user2: User
        +db_handler: DatabaseHandler
        +transaction_subject: TransactionSubject
        +__init__(user1, dbhandler, user2)
        +execute_transaction(payment_type, amount, to): str
    }
    
    TransactionObserver <|-- SMSNotificationObserver
    TransactionSubject o-- TransactionObserver
    TransactionOperation --> TransactionSubject
    TransactionOperation --> PaymentFactory
```
6. Database Management
```mermaid
classDiagram
    class DatabaseHandler {
        +file_path: str
        +__init__(file_path)
        +_initialize_db(): void
        +_read_data(): dict
        +_write_data(data): void
        +add_record(table, record, mapper): void
        +find_one(table, condition, mapper): object
        +find_many(table, condition, mapper): List
        +update_record(table, condition, update_func): bool
        +delete_record(table, condition): bool
        +read_data(table_name): List
        +save_data(table_name, record_data): void
        +get_next_id(counter_name): int
    }
    
    class DatabaseHandlerSingleton {
        <<singleton>>
        -_instance: DatabaseHandler
        +__new__(): DatabaseHandler
    }
    
    class UserSession {
        <<singleton>>
        -_instance: UserSession
        -_current_user: User
        +__new__(): UserSession
        +set_user(user): void
        +get_user(): User
        +clear_user(): void
    }
    
    DatabaseHandlerSingleton --> DatabaseHandler : creates
    UserSession --> User : manages
```
7. Data Mapper
```mermaid 
classDiagram
    class UserMapper {
        <<static>>
        +to_dict(user): dict
        +from_dict(data): User
    }
    
    class WalletMapper {
        <<static>>
        +to_dict(wallet): dict
        +from_dict(data): Wallet
    }
    
    class TransactionMapper {
        <<static>>
        +to_dict(tx): dict
        +from_dict(data): Transaction
    }
    
    class FamilyWalletMapper {
        <<static>>
        +to_dict(fw): dict
        +from_dict(data): FamilyWallet
        +update_member_in_family_wallet(db_handler, family_id, member_id, member_data): void
        +remove_member_from_family_wallet(db_handler, family_id, member_id): void
    }
    
    UserMapper ..> User : maps
    WalletMapper ..> Wallet : maps
    TransactionMapper ..> Transaction : maps
    FamilyWalletMapper ..> FamilyWallet : maps
```
8. Role Management
```mermaid
classDiagram
    class RegistrationFacade {
        +db_handler: DatabaseHandler
        +__init__()
        +register_user(user): str
        +login_user(phone, password): str
    }
    
    class FamilyWalletFacade {
        +family_wallet: FamilyWallet
        +db_handler: DatabaseHandler
        +child_account_manager: ChildAccountManager
        +__init__(family_wallet)
        +add_member(parent_user, child_phone, child_national_id, child_name, child_password, initial_limit): str
        +get_member_info(child_id): str
        +remove_member(child_id): str
        +set_limit(child_id, new_limit): str
        +see_history(child_id): void
        +see_all_children_history(): void
        +list_all_members(): str
    }
    
    class ChildAccountManager {
        +db_handler: DatabaseHandler
        +__init__(db_handler)
        +create_child_account(parent_user, child_phone, child_national_id, child_name, child_password): tuple
    }
    
    class RoleManager {
        <<static>>
        +calculate_age_from_national_id(national_id): int
        +can_change_to_parent(user): tuple[bool, str]
        +change_user_role(user, new_role, db_handler): str
    }
    
    RegistrationFacade --> DatabaseHandler
    RegistrationFacade --> ValidationCheck
    RegistrationFacade --> UserSession
    FamilyWalletFacade --> FamilyWallet
    FamilyWalletFacade --> DatabaseHandler
    FamilyWalletFacade --> ChildAccountManager
    ChildAccountManager --> DatabaseHandler
    ChildAccountManager --> ValidationCheck
    RoleManager --> Role
```
