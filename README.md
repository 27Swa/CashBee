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
