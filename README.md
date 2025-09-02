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

```mermaid
flowchart TD
    A[Register/Login] --> B["Wallet Home"]
    B --> C["Pay (QR / Phone)"]
    B --> D["Bill Payment"]
    B --> E[Family Wallet]
    B --> F[Donation]
    B --> G[Transaction Limits]
    B --> H["Transaction History"]
    B --> I["Collect Money"]
```
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

2. **Transaction Limits Configuration**
   - Parents set spending limits for each child individually
   - Establish family-wide transaction limits
   - Customize limits by transaction type (payments, donations, etc.)

3. **Financial Operations**
   - Direct Payments: Send money to contacts via QR code or phone number
   - Bill Payments: Utilities (electricity, water, gas) payment facility
   - Donations: Support approved charitable organizations
   - Money Collection: Request and receive funds from family members or contacts

4. **Transaction Monitoring & History**
   - All transactions are logged with detailed information
   - Filterable view by: child, date, transaction type, or amount
   - Real-time notifications for all financial activities

5. **Family Management**
   - Parents can add/remove family members
   - Customizable permissions for each family member
   - Centralized oversight of all family financial activities
