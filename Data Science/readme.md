# Fraud Detection 
## Dataset Information
- This dataset presents transactions that occurred in two days, where we have 492 frauds out of 284,807 transactions. The dataset is highly unbalanced, the positive class (frauds) account for 0.172% of all transactions.

- It contains only numerical input variables which are the result of a PCA transformation. Features V1, V2, … V28 are the principal components obtained with PCA, the only features which have not been transformed with PCA are 'Time' and 'Amount'. Feature 'Time' contains the seconds elapsed between each transaction and the first transaction in the dataset. The feature 'Amount' is the transaction Amount, this feature can be used for example-dependant cost-sensitive learning.

- Recommended: measuring the accuracy using the Area Under the Precision-Recall Curve (AUPRC). 

## Preprocessing Applied:
- Removing Duplicates
- Apply log on Amount column to remove noise from the data
- Apply Scalling on Amount, Time columns before appling models 
- See the precentage of outliers in all features for each class
- XGBoosting was used to apply feature importance 

## Training Models
- Start by taking top 10 features:
    - XGBoost acheived: 
        - AUC-PR: 0.8459
        - Precision: 
        - Recall: 
        - F2 score: 
    - Random Forest achieved:
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score:
    - Grid Search XGBoost acheived:
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score: 
    - Grid Search Random Forest achieved:
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score:

- Start by taking top 15 features:
    - XGBoost acheived: 
        - Precision: 0.9831
        - Recall: 0.8169
        - F2 score: 
        - AUC-PR: 0.8499
    - Random Forest achieved:
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score:
    - Grid Search XGBoost acheived:
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score: 
    - Grid Search Random Forest achieved:
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score:

- Start by taking top 20 features:
    - XGBoost acheived: 
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score: 
    - Random Forest achieved: 
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score:
    - Grid Search XGBoost acheived: 
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score: 
    - Grid Search Random Forest achieved: 
        - AUC-PR:
        - Precision: 
        - Recall: 
        - F2 score:
From previous result will get that its better to use 15 features and model XGBoost with parameters: 

## Saving model to use it later
- joblib library was used as it is fast and preserves full model