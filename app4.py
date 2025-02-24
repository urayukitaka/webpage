import os
import io
import shutil
import base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Flask上でmatplotlibを動かす場合のおまじない（GUIバックエンドを使わない）
import matplotlib.pyplot as plt
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # セッション管理用のシークレットキー

# ユーザーIDとパスワードを辞書形式で複数管理
users = {
    "user1": "pass1",
    "user2": "pass2",
    "admin": "admin"
}

#####################################
# サンプルデータの用意
#####################################

# メイン画面（ダッシュボード）で表示するログ用DataFrame
# 25件超のページングテストのため、あえて30行程度作る
main_data = {
    "ID": list(range(1, 31)),
    "Date": pd.date_range(start="2021-01-01", periods=30).astype(str),
    "Value": np.random.randint(100, 200, size=30),
    "Memo": [f"メモ{i}" for i in range(1, 31)]
}
df_main = pd.DataFrame(main_data)

# 4種類の異常検知ページで使う結果DataFrameを用意（本来は別々でもよいが、ここではサンプルとして共通の元データを使い回し）
# download 列は ZIP ダウンロードへのパス(実際には url_for で動的に生成してもOK)
result_data = {
    "RecordNo": list(range(1, 51)),
    "Product": [f"製品{i%3+1}" for i in range(50)],  # 3種類の製品
    "Score": np.round(np.random.rand(50) * 10, 2),
    "Memo": [f"結果メモ{i}" for i in range(1, 51)],
    # ダウンロード列 (本当は行ごとにパスを変えるなども可能)
    #"download": [r"data_157.zip" for _ in range(50)],
    "download": [r"data_19.zip" for _ in range(50)],
}
df_anomaly = pd.DataFrame(result_data)

#####################################
# 箱ひげ図生成用の関数
#####################################
def generate_boxplot(target_name):
    """
    指定された目的変数名に対応するサンプルの箱ひげ図を作成し、base64エンコードした文字列を返す
    """
    data = np.random.randn(50) * 10  # 適当なサンプルデータ
    plt.figure(figsize=(4, 3))
    plt.boxplot(data)
    plt.title(f"{target_name} の箱ひげ図")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# 目的変数3種(A, B, C)の静的画像(base64)をあらかじめ生成しておく
boxplot_imgs = {
    "目的変数A": generate_boxplot("目的変数A"),
    "目的変数B": generate_boxplot("目的変数B"),
    "目的変数C": generate_boxplot("目的変数C")
}

#####################################
# テンプレート (render_template_stringで定義)
#####################################

# ログインページ
login_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ログイン</title>
    <style>
      body { font-family: Arial, sans-serif; }
      .container { width: 300px; margin: 100px auto; }
      label { display: block; margin-top: 10px; }
      input { width: 100%; padding: 8px; margin-top: 5px; }
      button { margin-top: 15px; width: 100%; padding: 10px; }
      .error { color: red; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>ログイン</h2>
        <form method="post">
            <label for="username">ユーザーID</label>
            <input type="text" id="username" name="username" required>
            <label for="password">パスワード</label>
            <input type="password" id="password" name="password" required>
            <button type="submit">ログイン</button>
        </form>
        {% if error %}
          <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

# ダッシュボード（メイン画面）
dashboard_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>品質異常検知ダッシュボード</title>
    <style>
      body { font-family: Arial, sans-serif; background-color: #D0D0D0; color: #404040; }
      h1 { margin-left: 20px; }
      .container { display: flex; }
      .sidebar { width: 320px; background-color: #D0D0D0; padding: 20px; }
      .sidebar ul { list-style: none; padding: 0; font-size: 18px; }
      .sidebar li { margin-bottom: 15px; }
      .content { flex-grow: 1; padding: 20px; background-color: #F8F8F8; }

      /* テーブル周り */
      #filter-input {
          margin-bottom: 10px;
          padding: 5px;
          width: 100%;
          font-size: 16px;
      }
      .table-container {
          max-height: 600px;
          overflow-y: auto;
          border: 1px solid #aaa;
          background-color: white;
          position: relative;
      }
      .logtable {
          border-collapse: collapse;
          width: 100%;
          background-color: white;
          position: relative;
      }
      .logtable th, .logtable td {
          border: 1px solid #aaa;
          padding: 5px;
          text-align: left;
          white-space: nowrap; /* 折り返し防止 */
      }
      /* ヘッダー固定 */
      .logtable thead th {
          position: sticky;
          top: 0;
          background-color: #eee;
          z-index: 2;
      }
      /* ページネーション */
      .pagination {
          margin-top: 10px;
          text-align: center;
      }
      .pagination button {
          padding: 8px 12px;
          margin: 5px;
          font-size: 16px;
          cursor: pointer;
      }
      /* カラムソート用の見た目 */
      .sortable {
          cursor: pointer;
          background-color: #ddd;
      }
    </style>
</head>
<body>
    <h1>品質異常検知ダッシュボード</h1>
    <div class="container">
        <!-- サイドバー -->
        <div class="sidebar">
            <ul>
                <li>
                    <strong>異常検知1:</strong> ValueA<br>
                    <a href="{{ url_for('anomaly_page', anomaly_id=1) }}">[ページへ]</a>
                </li>
                <li>
                    <strong>異常検知2:</strong> ValueB<br>
                    <a href="{{ url_for('anomaly_page', anomaly_id=2) }}">[ページへ]</a>
                </li>
                <li>
                    <strong>異常検知3:</strong> ValueC<br>
                    <a href="{{ url_for('anomaly_page', anomaly_id=3) }}">[ページへ]</a>
                </li>
                <li>
                    <strong>異常検知4:</strong> ValueD<br>
                    <a href="{{ url_for('anomaly_page', anomaly_id=4) }}">[ページへ]</a>
                </li>
            </ul>
        </div>
        <!-- メインコンテンツ -->
        <div class="content">
            <h2>ログ一覧</h2>
            <input type="text" id="filter-input" placeholder="検索キーワードを入力" onkeyup="filterTable()">
            <div class="table-container">
                <table class="logtable" id="log-table">
                    <thead>
                        <tr>
                            <!-- ソート可能カラムに sortable クラスを付与 -->
                            <th class="sortable" onclick="sortTable(0)">ID</th>
                            <th class="sortable" onclick="sortTable(1)">Date</th>
                            <th class="sortable" onclick="sortTable(2)">Value</th>
                            <th class="sortable" onclick="sortTable(3)">Memo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in table_data %}
                        <tr>
                            <td>{{ row["ID"] }}</td>
                            <td>{{ row["Date"] }}</td>
                            <td>{{ row["Value"] }}</td>
                            <td>{{ row["Memo"] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- ページネーション -->
            <div class="pagination">
                <button onclick="prevPage()">« 前のページ</button>
                <span id="page-info"></span>
                <button onclick="nextPage()">次のページ »</button>
            </div>
        </div>
    </div>

    <script>
        // ページングやフィルタ関連変数
        let rowsPerPage = 25;  // 1ページあたりの行数
        let currentPage = 1;
        let tableBody = document.querySelector("#log-table tbody");
        let allRows = Array.from(tableBody.getElementsByTagName("tr"));
        let filteredRows = [...allRows];

        // テーブルを再描画する
        function updateTable() {
            tableBody.innerHTML = "";
            let start = (currentPage - 1) * rowsPerPage;
            let end = start + rowsPerPage;
            let rowsToShow = filteredRows.slice(start, end);
            rowsToShow.forEach(row => tableBody.appendChild(row));
            document.getElementById("page-info").innerText =
                `ページ ${currentPage} / ${Math.max(1, Math.ceil(filteredRows.length / rowsPerPage))}`;
        }

        // フィルター(キーワード検索)
        function filterTable() {
            let keyword = document.getElementById("filter-input").value.toLowerCase();
            filteredRows = allRows.filter(row => {
                return Array.from(row.getElementsByTagName("td")).some(td => {
                    return td.textContent.toLowerCase().includes(keyword);
                });
            });
            currentPage = 1;
            updateTable();
        }

        // ページ送り
        function nextPage() {
            if (currentPage * rowsPerPage < filteredRows.length) {
                currentPage++;
                updateTable();
            }
        }
        function prevPage() {
            if (currentPage > 1) {
                currentPage--;
                updateTable();
            }
        }

        // カラムソート
        // colIndex は列番号(0始まり)
        // 数値判定は簡易チェックにしている
        function sortTable(colIndex) {
            let isNumberColumn = true;
            // 先頭行で数値かどうかを判定する
            let firstRowValue = filteredRows[0].getElementsByTagName("td")[colIndex].innerText.trim();
            if (isNaN(parseFloat(firstRowValue))) {
                isNumberColumn = false;
            }
            // ソート実行（単純昇順ソートとして実装）
            filteredRows.sort((a, b) => {
                let aText = a.getElementsByTagName("td")[colIndex].innerText.trim();
                let bText = b.getElementsByTagName("td")[colIndex].innerText.trim();
                if(isNumberColumn) {
                    return parseFloat(aText) - parseFloat(bText);
                } else {
                    return aText.localeCompare(bText, 'ja');
                }
            });
            currentPage = 1;
            updateTable();
        }

        // 初期表示
        updateTable();
    </script>
</body>
</html>
"""

# 各異常検知ページのテンプレート
anomaly_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{{ anomaly_name }}</title>
    <style>
      body { font-family: Arial, sans-serif; background-color: #D0D0D0; color: #404040; }
      .container { width: 95%; margin: 20px auto; background-color: #F8F8F8; padding: 20px; }
      .top-nav { margin-bottom: 10px; }
      .dropdown { margin-bottom: 10px; }
      .boxplot-area { margin-bottom: 20px; }

      /* テーブルデザイン */
      #filter-input {
          margin-bottom: 10px;
          padding: 5px;
          width: 100%;
          font-size: 16px;
      }
      .table-container {
          max-height: 400px;
          overflow-y: auto;
          border: 1px solid #aaa;
          background-color: white;
          position: relative;
      }
      .result-table {
          border-collapse: collapse;
          width: 100%;
          background-color: white;
      }
      .result-table th, .result-table td {
          border: 1px solid #aaa;
          padding: 5px;
          text-align: left;
          white-space: nowrap; /* 折り返し防止 */
      }
      /* ヘッダー固定 */
      .result-table thead th {
          position: sticky;
          top: 0;
          background-color: #eee;
          z-index: 2;
      }
      /* ページネーション */
      .pagination {
          margin-top: 10px;
          text-align: center;
      }
      .pagination button {
          padding: 8px 12px;
          margin: 5px;
          font-size: 16px;
          cursor: pointer;
      }
      /* カラムソート用 */
      .sortable {
          cursor: pointer;
          background-color: #ddd;
      }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-nav">
            <a href="{{ url_for('dashboard') }}">← 前の画面に戻る</a>
        </div>
        <h1>{{ anomaly_name }}</h1>

        <!-- 製品群ドロップダウン（サンプル） -->
        <div class="dropdown">
            <label>製品群を選択: </label>
            <select id="product-dropdown" onchange="onChangeProduct()">
                <option value="すべて">すべて</option>
                <option value="製品1">製品1</option>
                <option value="製品2">製品2</option>
                <option value="製品3">製品3</option>
            </select>
        </div>

        <!-- 箱ひげ図エリア -->
        <div class="boxplot-area">
            <label>目的変数選択:</label>
            <select id="target-dropdown" onchange="switchBoxplot()">
                <option value="A">目的変数A</option>
                <option value="B">目的変数B</option>
                <option value="C">目的変数C</option>
            </select>
            <div>
                <img id="plot-A" src="data:image/png;base64,{{ boxplot_imgs['目的変数A'] }}" style="display:block; max-width:400px;">
                <img id="plot-B" src="data:image/png;base64,{{ boxplot_imgs['目的変数B'] }}" style="display:none; max-width:400px;">
                <img id="plot-C" src="data:image/png;base64,{{ boxplot_imgs['目的変数C'] }}" style="display:none; max-width:400px;">
            </div>
        </div>

        <!-- 結果テーブル -->
        <h2>検知結果</h2>
        <input type="text" id="filter-input" placeholder="検索キーワードを入力" onkeyup="filterTable()">
        <div class="table-container">
            <table class="result-table" id="result-table">
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(0)">RecordNo</th>
                        <th class="sortable" onclick="sortTable(1)">Product</th>
                        <th class="sortable" onclick="sortTable(2)">Score</th>
                        <th class="sortable" onclick="sortTable(3)">Memo</th>
                        <th>Download</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_data %}
                    <tr>
                        <td>{{ row["RecordNo"] }}</td>
                        <td>{{ row["Product"] }}</td>
                        <td>{{ row["Score"] }}</td>
                        <td>{{ row["Memo"] }}</td>
                        <td>{{ row["download"]|safe }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- ページネーション -->
        <div class="pagination">
            <button onclick="prevPage()">« 前のページ</button>
            <span id="page-info"></span>
            <button onclick="nextPage()">次のページ »</button>
        </div>
    </div>

    <script>
        // ----- 箱ひげ図の切り替え -----
        function switchBoxplot() {
            let val = document.getElementById("target-dropdown").value;
            document.getElementById("plot-A").style.display = (val === "A") ? "block" : "none";
            document.getElementById("plot-B").style.display = (val === "B") ? "block" : "none";
            document.getElementById("plot-C").style.display = (val === "C") ? "block" : "none";
        }

        // ----- 製品群のドロップダウン変更 -----
        // 本来はサーバーサイドで絞り込んで再描画するなどする想定ですが、
        // ここではフロント側の簡単なフィルターにとどめます
        function onChangeProduct() {
            applyAllFilters();
        }

        // ----- テーブルのフィルター & ページング & ソート -----
        let rowsPerPage = 25;
        let currentPage = 1;
        let tableBody = document.querySelector("#result-table tbody");
        let allRows = Array.from(tableBody.getElementsByTagName("tr"));
        let filteredRows = [...allRows];

        // 追加で「製品群」ドロップダウンの値によるフィルタ
        function applyAllFilters() {
            let keyword = document.getElementById("filter-input").value.toLowerCase();
            let productSelected = document.getElementById("product-dropdown").value;
            filteredRows = allRows.filter(row => {
                let tds = row.getElementsByTagName("td");
                let rowText = row.textContent.toLowerCase();
                let passKeyword = (keyword === "") ? true : rowText.includes(keyword);

                // 製品の列は2番目(tdインデックス1)である想定
                let productVal = tds[1].textContent.trim();
                let passProduct = (productSelected === "すべて" || productVal === productSelected);

                return passKeyword && passProduct;
            });
            currentPage = 1;
            updateTable();
        }

        function filterTable() {
            applyAllFilters();
        }

        function updateTable() {
            tableBody.innerHTML = "";
            let start = (currentPage - 1) * rowsPerPage;
            let end = start + rowsPerPage;
            let rowsToShow = filteredRows.slice(start, end);
            rowsToShow.forEach(row => tableBody.appendChild(row));
            document.getElementById("page-info").innerText =
                `ページ ${currentPage} / ${Math.max(1, Math.ceil(filteredRows.length / rowsPerPage))}`;
        }

        function nextPage() {
            if (currentPage * rowsPerPage < filteredRows.length) {
                currentPage++;
                updateTable();
            }
        }

        function prevPage() {
            if (currentPage > 1) {
                currentPage--;
                updateTable();
            }
        }

        // ソート(簡単な昇順ソートのみ)
        function sortTable(colIndex) {
            // 先頭行が数値か文字列か判定
            let firstRowValue = filteredRows[0].getElementsByTagName("td")[colIndex].innerText.trim();
            let isNumber = !isNaN(parseFloat(firstRowValue));

            filteredRows.sort((a, b) => {
                let aVal = a.getElementsByTagName("td")[colIndex].innerText.trim();
                let bVal = b.getElementsByTagName("td")[colIndex].innerText.trim();
                if(isNumber) {
                    return parseFloat(aVal) - parseFloat(bVal);
                } else {
                    return aVal.localeCompare(bVal, 'ja');
                }
            });
            currentPage = 1;
            updateTable();
        }

        // 初期表示
        updateTable();
    </script>
</body>
</html>
"""

#####################################
# Flaskルーティング
#####################################

# ルート: ログインページ
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # ユーザーIDが辞書に存在し、パスワードが一致するかチェック
        if username in users and users[username] == password:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "ユーザーIDまたはパスワードが違います。"
    return render_template_string(login_template, error=error)

# ダッシュボード（メイン画面）
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    # df_main をテンプレートに渡してテーブル表示
    table_data = df_main.to_dict(orient="records")
    return render_template_string(dashboard_template, table_data=table_data)

# 異常検知ページ(4種類)
@app.route("/anomaly/<int:anomaly_id>")
def anomaly_page(anomaly_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    # anomaly_id に応じて名称を変更(サンプル)
    if anomaly_id == 1:
        anomaly_name = "異常検知1: ValueA"
    elif anomaly_id == 2:
        anomaly_name = "異常検知2: ValueB"
    elif anomaly_id == 3:
        anomaly_name = "異常検知3: ValueC"
    elif anomaly_id == 4:
        anomaly_name = "異常検知4: ValueD"
    else:
        anomaly_name = f"異常検知{anomaly_id}: 未定義"

    # df_anomaly をテンプレートに渡す
    # ダウンロードリンクはHTMLタグを埋め込む
    df_display = df_anomaly.copy()
    df_display["download"] = df_display["download"].apply(lambda x: f'<a href="/download/{x}">ダウンロード</a>')

    table_data = df_display.to_dict(orient="records")
    return render_template_string(
        anomaly_template,
        anomaly_name=anomaly_name,
        table_data=table_data,
        boxplot_imgs=boxplot_imgs
    )

# ZIPファイルダウンロード (静的ファイルsample.zipへのアクセス)
@app.route("/download/<path:filename>")
def download_file(filename):
    # staticフォルダ内のファイルをダウンロード可能にする
    # copy
    filename_ = os.path.join("./data/datalog", filename)
    basename = os.path.basename(filename_)
    shutil.copy(filename_, os.path.join("./src/download", basename))
    return send_from_directory(directory="download", path=filename, as_attachment=True)

#####################################
# メイン
#####################################
if __name__ == "__main__":
    # アプリ起動
    # 静的フォルダに sample.zip を置いておくことでダウンロードリンク動作を確認できます
    app.run(debug=True)
