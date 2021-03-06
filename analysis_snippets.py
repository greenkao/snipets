import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sn
from sklearn.metrics import confusion_matrix
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.grid_search import GridSearchCV
from imblearn.ensemble import BalancedRandomForestClassifier
from IPython.display import display

#%matplotlib inline
#plt.style.use('ggplot')
#plt.rcParams['font.family'] = 'IPAexGothic'


def hml_kmeans(clst_list, n_clst):
    # HML用のkmeansクラスタリング
    # クラスタ結果の表示、クラスタ番号を平均の高い順に変更する

    RANDOM_STATE = 123
    vector_array = np.array(clst_list)
    ROWS_NUM = len(vector_array)
    vector_array = vector_array.reshape(ROWS_NUM, 1)

    clusters = KMeans(n_clusters=n_clst, random_state=RANDOM_STATE).fit_predict(vector_array)

    # 元のリストとクラスタでpd.DataFrameの作成
    clst_df = pd.DataFrame({"var": clst_list, "cluster": clusters})

    # クラスタ毎の統計量を確認し、デフォルトではmeanでクラスタ番号を昇順に
    clst_result = clst_df.groupby(["cluster"])["var"].agg(["mean", "count", "min", "max", "median"]).reset_index()
    clst_result['rank_by_mean'] = clst_result["mean"].rank(ascending=False).astype("int")
    display(clst_result)
    convert_rules = dict(clst_result.set_index("cluster").rank_by_mean)

    return list(clst_df["cluster"].map(convert_rules))


def print_cmx(y_true, y_pred, labels):

    # めっちゃ綺麗な混合行列を出力する関数
    # ヒートマップ機能付き

    cmx_data = confusion_matrix(y_true, y_pred, labels=labels)
    print(cmx_data)
    df_cmx = pd.DataFrame(cmx_data, index=labels, columns=labels)

    plt.figure(figsize=(6, 4.5))
    plt.rcParams['font.size'] = 15
    sn.heatmap(df_cmx, cmap='Reds', annot=True, fmt="d", xticklabels=True, yticklabels=True)
    # plt.savefig('heatmap.png')
    ax = plt.gca()
    ax.xaxis.set_ticks_position("top")  # x軸目盛りは軸の上、bottomで下になる
    ax.set_yticklabels(reversed(labels), rotation=0)
    ax.set_xlabel("predicted label")
    ax.set_ylabel("real label")
    plt.show()


def RF_classifier(df, y_column, feature_columns, test_rate):

    # クラス分類用ランダムフォレスト
    # 混合行列や重要度の高い変数を可視化する

    # 説明変数、目的変数の作成
    X = df.loc[:, feature_columns].values
    Y = df.loc[:, y_column].values

    # 学習用、検証用データに分割
    (X_train, X_test, Y_train, Y_test) = train_test_split(X, Y, test_size=test_rate, random_state=123)

    '''
    # モデル構築、パラメータはデフォルト
    parameters = {
        'n_estimators'      : [5, 10, 20, 30, 50],
        'max_features'      : [3, 5, 10, 15, 20],
        'random_state'      : [0],
        'n_jobs'            : [2],
        'min_samples_split' : [3, 5, 10, 15, 20, 25, 30],
        'max_depth'         : [3, 5, 10, 15, 20, 25, 30, 50, 100]
    }

    clf = GridSearchCV(RandomForestClassifier(), parameters)
    clf.fit(X_train, Y_train)
    print(clf.best_estimator_)'''

    model = RandomForestClassifier(n_estimators=20, max_depth=4, max_features=None, bootstrap=True)

    print(model.get_params())
    model.fit(X_train, Y_train)

    # 正解率
    print("正解率 : " + str(model.score(X_test, Y_test) * 100) + "%")
    print("訓練データの正解率 : " + str(model.score(X_train, Y_train) * 100) + "%")

    # confusion matrix　を確認する
    print("confusion matrix")
    prediction = model.predict(X_test)
    labels = list(set(Y))
    print_cmx(Y_test, prediction, labels)

    # 効いてる変数を順に並べる
    importances = pd.DataFrame(
        {
            'variable': feature_columns,
            'importance': model.feature_importances_
        }
    ).sort_values('importance', ascending=False).reset_index(drop=True)
    display(importances)

    IMP = importances.copy()
    plt.figure(figsize=(5, 7))
    plt.plot(IMP.importance, sorted([i + 1 for i in range(IMP.shape[0])], reverse=True), 'o-')
    plt.yticks(sorted([i + 1 for i in range(IMP.shape[0])], reverse=True), IMP.variable)
    plt.xlabel('importance')
    # plt.xlabel('重要度')
    plt.show()

    return importances


def lassocv_reg(df, x_vars, y_var, test_size=0.2):
    """
    instant Lasso Regression CV
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LassoCV
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error
    import numpy as np
    
    X = df[x_vars]
    y = df[y_var]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=123)
    scaler = StandardScaler()
    clf = LassoCV(alphas=10 ** np.arange(-6, 1, 0.1), cv=5)

    scaler.fit(X_train)
    clf.fit(scaler.transform(X_train), y_train)
    
    # score
    y_pred = clf.predict(scaler.transform(X_test))
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f'rmse score: {rmse}')
    
    # coefs
    coefs = pd.DataFrame(
        {
            'variable': x_vars,
            'coefs': clf.coef_.tolist(),
        }).sort_values('coefs', ascending=False).reset_index(drop=True)
    plt.figure(figsize=(5, 7))
    plt.plot(coefs['coefs'], sorted([i + 1 for i in range(coefs.shape[0])], reverse=True), 'o-')
    plt.yticks(sorted([i + 1 for i in range(coefs.shape[0])], reverse=True), coefs['variable'])
    plt.xlabel('coefs')
    plt.show()
    
    coefs = pd.DataFrame(
        {
            'variable': x_vars,
            'coefs': np.abs(clf.coef_.tolist()),
        }).sort_values('coefs', ascending=False).reset_index(drop=True)
    plt.figure(figsize=(5, 7))
    plt.plot(coefs['coefs'], sorted([i + 1 for i in range(coefs.shape[0])], reverse=True), 'o-')
    plt.yticks(sorted([i + 1 for i in range(coefs.shape[0])], reverse=True), coefs['variable'])
    plt.xlabel('abs coefs')
    plt.show()
    

    
 
def simple_dtree(df, x_list, y_var, max_depth=3, regressor=False, min_samples_split=2, test_size=0.3):
    """
    instant DecisionTree model
    """
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.tree import  DecisionTreeClassifier
    from sklearn.model_selection import train_test_split
    from dtreeviz.trees import dtreeviz

    X = df[x_list]
    y = df[y_var]
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=123, test_size=test_size)

    # build model, and fitting
    if regressor:
        model = DecisionTreeRegressor(max_depth=max_depth, random_state=123, min_samples_split=min_samples_split)
    else:
        model = DecisionTreeClassifier(max_depth=max_depth, random_state=123, min_samples_split=min_samples_split)
    model.fit(X_train, y_train)

    # plot
    print('Train score: {:.3f}'.format(model.score(X_train, y_train)))
    print('Test score: {:.3f}'.format(model.score(X_test, y_test)))
    viz = dtreeviz(
        model,
        X_train=X,
        y_train=y,
        target_name=y_var,
        feature_names=x_list,
        precision=2,
        class_names=None if model.classes_ is None else model.classes_.tolist(),
    ) 
    viz.view()
    return model


def BalancedRF_classifier(df, y_column, feature_columns, test_rate):

    # 不均衡クラス分類用ランダムフォレスト
    # 混合行列や重要度の高い変数を可視化する

    # 説明変数、目的変数の作成
    X = df.loc[:, feature_columns].values
    Y = df.loc[:, y_column].values

    # 学習用、検証用データに分割
    (X_train, X_test, Y_train, Y_test) = train_test_split(X, Y, test_size=test_rate, random_state=123, shuffle=True)

    '''
    # モデル構築、パラメータはデフォルト
    parameters = {
        'n_estimators'      : [5, 10, 20, 30, 50],
        'max_features'      : [3, 5, 10, 15, 20],
        'random_state'      : [0],
        'n_jobs'            : [2],
        'min_samples_split' : [3, 5, 10, 15, 20, 25, 30],
        'max_depth'         : [3, 5, 10, 15, 20, 25, 30, 50, 100]
    }
    clf = GridSearchCV(RandomForestClassifier(), parameters)
    clf.fit(X_train, Y_train)
    print(clf.best_estimator_)'''

    model = BalancedRandomForestClassifier(n_jobs=1, n_estimators=30, sampling_strategy='not minority')   

    print(model.get_params())
    model.fit(X_train, Y_train)

    # 正解率
    print("正解率 : " + str(model.score(X_test, Y_test) * 100) + "%")
    print("訓練データの正解率 : " + str(model.score(X_train, Y_train) * 100) + "%")

    # confusion matrix　を確認する
    print("confusion matrix")
    prediction = model.predict(X_test)
    labels = list(set(Y))
    print_cmx(Y_test, prediction, labels)

    # 効いてる変数を調べる
    importances = None
    i = np.array([
        e['classifier'].feature_importances_
        
        for e in model.estimators_ 
    ])
    avg_i = np.array([
        e['classifier'].feature_importances_
        for e in model.estimators_ 
    ]).mean(axis=0)
    importances = plot_importance(avg_i, feature_columns)

    return model, importances, (X_train, X_test, Y_train, Y_test)

    
def plot_decision_path(tree_model, df, x_vars):
    X = np.array(df[x_vars])
    # Using those arrays, we can parse the tree structure:
    # copy from: https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html

    n_nodes = tree_model.tree_.node_count
    children_left = tree_model.tree_.children_left
    children_right = tree_model.tree_.children_right
    feature = tree_model.tree_.feature
    threshold = tree_model.tree_.threshold


    # The tree structure can be traversed to compute various properties such
    # as the depth of each node and whether or not it is a leaf.
    node_depth = np.zeros(shape=n_nodes, dtype=np.int64)
    is_leaves = np.zeros(shape=n_nodes, dtype=bool)
    stack = [(0, -1)]  # seed is the root node id and its parent depth
    while len(stack) > 0:
        node_id, parent_depth = stack.pop()
        node_depth[node_id] = parent_depth + 1

        # If we have a test node
        if (children_left[node_id] != children_right[node_id]):
            stack.append((children_left[node_id], parent_depth + 1))
            stack.append((children_right[node_id], parent_depth + 1))
        else:
            is_leaves[node_id] = True

    print("The binary tree structure has %s nodes and has "
          "the following tree structure:"
          % n_nodes)
    for i in range(n_nodes):
        if is_leaves[i]:
            print("%snode=%s leaf node." % (node_depth[i] * "\t", i))
        else:
            print("%snode=%s test node: go to node %s if X[:, %s] <= %s else to "
                  "node %s."
                  % (node_depth[i] * "\t",
                     i,
                     children_left[i],
                     feature[i],
                     threshold[i],
                     children_right[i],
                     ))
    print()

    # First let's retrieve the decision path of each sample. The decision_path
    # method allows to retrieve the node indicator functions. A non zero element of
    # indicator matrix at the position (i, j) indicates that the sample i goes
    # through the node j.

    node_indicator = tree_model.decision_path(X)

    # Similarly, we can also have the leaves ids reached by each sample.

    leave_id = tree_model.apply(X)

    # Now, it's possible to get the tests that were used to predict a sample or
    # a group of samples. First, let's make it for the sample.

    sample_id = 0
    node_index = node_indicator.indices[node_indicator.indptr[sample_id]:
                                        node_indicator.indptr[sample_id + 1]]

    print('Rules used to predict sample %s: ' % sample_id)
    for node_id in node_index:
        if leave_id[sample_id] == node_id:
            continue

        if (X[sample_id, feature[node_id]] <= threshold[node_id]):
            threshold_sign = "<="
        else:
            threshold_sign = ">"

        print("decision id node %s : (X[%s, %s] (= %s) %s %s)"
              % (node_id,
                 sample_id,
                 feature[node_id],
                 X[sample_id, feature[node_id]],
                 threshold_sign,
                 threshold[node_id]))

    # For a group of samples, we have the following common node.
    sample_ids = [0, 1]
    common_nodes = (node_indicator.toarray()[sample_ids].sum(axis=0) ==
                    len(sample_ids))
    common_node_id = np.arange(n_nodes)[common_nodes]

    print("\nThe following samples %s share the node %s in the tree"
          % (sample_ids, common_node_id))
    print("It is %s %% of all nodes." % (100 * len(common_node_id) / n_nodes,))
