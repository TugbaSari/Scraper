import pymssql
import pandas as pd
from pandas.tools.plotting import scatter_matrix
import matplotlib.pyplot as plt
from sklearn import model_selection
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

db = None


def init_db():
    global db
    if db is None:
        db = pymssql.connect(server='localhost\SQL2014', user='ts', password='test', database='funda')


def get_analysis_data():
    init_db()
    cursor = db.cursor(as_dict=True)
    query = """select construction_year, price_range, living_area, area_code, area_id, house_types, energy_label
               from dbo.house_analysis"""
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data


dataset = get_analysis_data()
number_of_rows = len(dataset)
dataframe = pd.DataFrame(dataset)

fig, ax = plt.subplots()
scatter_matrix(dataframe, ax=ax)
plt.show()
fig.savefig('./cross_matrix15.png')

fig, ax = plt.subplots()
dataframe.plot(kind='box', subplots=True, layout=(3, 3), sharex=False, sharey=False, ax=ax)
plt.show()
fig.savefig('./box_plot5.png')

fig, ax = plt.subplots()
dataframe.hist(ax=ax)
plt.show()
fig.savefig('./cross_hist5.png')

array = dataframe.values
X = array[:, 0:6]
Y = array[:, 6]
validation_size = 0.20
seed = 7
X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size,
                                                                                random_state=seed)

seed = 7
scoring = 'accuracy'

models = [('LR', LogisticRegression()),
          ('LDA', LinearDiscriminantAnalysis()),
          ('KNN', KNeighborsClassifier()),
          ('CART', DecisionTreeClassifier()),
          ('NB', GaussianNB()),
          ('SVM', SVC())]
# evaluate each model in turn
results = []
names = []
for name, model in models:
    kfold = model_selection.KFold(n_splits=10, random_state=seed)
    cv_results = model_selection.cross_val_score(model, X_train, Y_train, cv=kfold, scoring=scoring)
    results.append(cv_results)
    names.append(name)
    msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
    print(msg)

fig = plt.figure()
fig.suptitle('Algorithm Comparison')
ax = fig.add_subplot(111)
plt.boxplot(results)
ax.set_xticklabels(names)
plt.show()

knn = KNeighborsClassifier()
knn.fit(X_train, Y_train)
predictions = knn.predict(X_validation)
print(accuracy_score(Y_validation, predictions))
print(confusion_matrix(Y_validation, predictions))
print(classification_report(Y_validation, predictions))
