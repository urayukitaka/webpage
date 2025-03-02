import os
import numpy as np
import pandas as pd
from flask import (
    Flask, render_template_string, request, redirect,
    url_for, session, send_from_directory
)
import config as c

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ユーザーIDとパスワードを管理
users = {
    "user1": "pass1",
    "user2": "pass2",
    "admin": "admin"
}

#####################################
# サンプルデータの用意
#####################################

# メイン画面（ダッシュボード）に表示するDataFrame
df_main = pd.DataFrame({
    "ID": list(range(1, 31)),
    "Date": pd.date_range(start="2021-01-01", periods=30).astype(str),
    "Value": np.random.randint(100, 200, size=30),
    "Memo": [f"メモ{i}" for i in range(1, 31)]
})

# 異常検知結果用DataFrameを読み込み
df_result = pd.read_csv(r"data\detection_tbl.csv", encoding="CP932")

# DetectionType for page
detection_type = {"detectA": 1, "detectB": 2, "detectC": 3, "detectD": 4}
df_result["DetectionType"] = df_result["detect_category"].map(detection_type)

def convert_graphpath(old_path: str) -> str:
    """
    例:
      CSVのold_pathが
         1) "data/graphs\data_0\graph.png"  (相対っぽい)
         2) "C:\\Users\\...\\data\\graphs\\data_0\\graph.png" (絶対パス)
      と混在していると想定。

    1) と 2) のどちらでも動くように工夫:
      - まず "/" を "\\" に統一
      - "graphs\\" の位置を探して、それ以降を取り出す (例: "data_0\\graph.png")
      - それを "/my_images/data_0/graph.png" に変換
    """
    # まず混在しているかもしれない "/" を "\\" に揃える
    unified = old_path.replace("/", "\\")

    # 大文字小文字を気にしないで "graphs\\" を探す (見つかればその直後を取り出す)
    # 例:  unified = "data\\graphs\\data_0\\graph.png"
    #      idx = unified.lower().find("graphs\\") → idxを見つける
    #      subpart = unified[idx+len("graphs\\"):] → "data_0\\graph.png"
    # もし "graphs\\" が無い場合は仕方ないので basenameだけ、等の処理をする
    lower_unified = unified.lower()
    keyword = "graphs\\"
    idx = lower_unified.find(keyword)
    if idx == -1:
        # "graphs\" が見つからない場合、仕方ないので最後2要素を使うなど最低限の対応
        # 例: "data_0\\graph.png" 風になっていればOK
        # あるいは "old_path" 全体を扱うようにする
        # ここは環境やCSVの実際の書き方に合わせて調整
        subpart = os.path.basename(unified)
    else:
        # "graphs\\"より後ろの文字列を取得
        # 例: "data_0\\graph.png"
        start = idx + len(keyword)  # graphs\ の直後
        subpart = unified[start:]   # 例: "data_0\\graph.png"

    # subpart = "data_0\\graph.png" のようになったと想定
    # URLパスとして使うので、さらに "/" に変換
    sub_url = subpart.replace("\\", "/")
    # 例えば "data_0/graph.png"

    # Flask用の絶対パス → "/my_images/data_0/graph.png"
    return f"/my_images/{sub_url}"

# CSVのgraphpathを変換
df_result["graphpath"] = df_result["graphpath"].apply(convert_graphpath)

# ZIPファイルの列名を変更
df_result.rename(columns={"zipfile": "download"}, inplace=True)
df_result["download"] = [os.path.basename(p) for p in df_result["download"]]

# 列の並びを再定義
df_result = df_result[[
    "no","DetectionType","product","test","score","judge",
    "lcl","ucl","download","graphpath"
]]

#####################################
# テンプレート
#####################################
login_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ログイン</title>
    <style>
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

dashboard_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>品質異常検知ダッシュボード</title>
    <style>
      body { font-family: Arial, sans-serif; background-color: #D0D0D0; color: #404040; }
      .container { display: flex; }
      .sidebar { width: 320px; background-color: #D0D0D0; padding: 20px; }
      .content { flex-grow: 1; padding: 20px; background-color: #F8F8F8; }
      #filter-input { margin-bottom: 10px; padding: 5px; width: 100%; font-size: 16px; }
      .table-container { max-height: 600px; overflow-y: auto; border: 1px solid #aaa; background-color: white; position: relative; }
      .logtable { table-layout : fixed; border-collapse: collapse; width: 100%; background-color: white; }
      .logtable th, .logtable td { border: 1px solid #aaa; padding: 5px; text-align: left; white-space: nowrap; }
      .logtable thead th { position: sticky; top: 0; background-color: #eee; z-index: 2; }
      .pagination { margin-top: 10px; text-align: center; }
      .pagination button { padding: 8px 12px; margin: 5px; font-size: 16px; cursor: pointer; }
      .sortable { cursor: pointer; background-color: #ddd; }
    </style>
</head>
<body>
    <h1>品質異常検知ダッシュボード</h1>
    <div class="container">
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
        <div class="content">
            <h2>ログ一覧</h2>
            <input type="text" id="filter-input" placeholder="検索キーワードを入力" onkeyup="filterTable()">
            <div class="table-container">
                <table class="logtable" id="log-table">
                    <thead>
                        <tr>
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
            <div class="pagination">
                <button onclick="prevPage()">« 前のページ</button>
                <span id="page-info"></span>
                <button onclick="nextPage()">次のページ »</button>
            </div>
        </div>
    </div>
    <script>
        let rowsPerPage = 25;
        let currentPage = 1;
        let tableBody = document.querySelector("#log-table tbody");
        let allRows = Array.from(tableBody.getElementsByTagName("tr"));
        let filteredRows = [...allRows];

        function updateTable() {
            tableBody.innerHTML = "";
            let start = (currentPage - 1) * rowsPerPage;
            let end = start + rowsPerPage;
            let rowsToShow = filteredRows.slice(start, end);
            rowsToShow.forEach(row => tableBody.appendChild(row));
            document.getElementById("page-info").innerText =
                `ページ ${currentPage} / ${Math.max(1, Math.ceil(filteredRows.length / rowsPerPage))}`;
        }

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

        function sortTable(colIndex) {
            if (filteredRows.length === 0) return;
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
        updateTable();
    </script>
</body>
</html>
"""

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
      .graph-area { margin: 15px 0; }
      #filter-input { margin-bottom: 10px; padding: 5px; width: 100%; font-size: 16px; }
      .table-container { max-height: 600px; overflow-y: auto; border: 1px solid #aaa; background-color: white; position: relative; }
      .result-table { table-layout : fixed; border-collapse: collapse; width: 100%; background-color: white; }
      .result-table th, .result-table td {
          border: 1px solid #aaa; padding: 5px; text-align: left; white-space: nowrap;
      }
      .result-table thead th {
          position: sticky; top: 0; background-color: #eee; z-index: 2;
      }
      .pagination { margin-top: 10px; text-align: center; }
      .pagination button { padding: 8px 12px; margin: 5px; font-size: 16px; cursor: pointer; }
      .sortable { cursor: pointer; background-color: #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-nav">
            <a href="{{ url_for('dashboard') }}">← 前の画面に戻る</a>
        </div>
        <h1>{{ anomaly_name }}</h1>

        <!-- 左右2カラムで配置 -->
        <div style="display: flex; align-items: flex-start;">
            <!-- 左カラム -->
            <div style="margin-right: 30px;">
                <h3>トレンドグラフ確認</h3>
                <div class="dropdown">
                    <label>製品群を選択: </label>
                    <select id="product-select"></select>
                </div>
                <div class="dropdown">
                    <label>目的変数を選択: </label>
                    <select id="test-select"></select>
                </div>
                <div>
                    <button onclick="showGraph()">表示</button>
                </div>
            </div>

            <!-- 右カラム(グラフ表示エリア) -->
            <div style="flex-grow: 1;">
                <div class="graph-area">
                    <img id="graph-display" src="" alt="グラフ" style="max-width: 2000px; display: block;">
                </div>
            </div>
        </div>

        <h2>検知結果</h2>
        <input type="text" id="filter-input" placeholder="検索キーワードを入力" onkeyup="filterTable()">
        <div class="table-container">
            <table class="result-table" id="result-table">
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(0)">no</th>
                        <th class="sortable" onclick="sortTable(1)">product</th>
                        <th class="sortable" onclick="sortTable(2)">test</th>
                        <th class="sortable" onclick="sortTable(3)">score</th>
                        <th class="sortable" onclick="sortTable(4)">judge</th>
                        <th class="sortable" onclick="sortTable(5)">lcl</th>
                        <th class="sortable" onclick="sortTable(6)">ucl</th>
                        <th>Download</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_data %}
                    <tr>
                        <td>{{ row["no"] }}</td>
                        <td>{{ row["product"] }}</td>
                        <td>{{ row["test"] }}</td>
                        <td>{{ row["score"] }}</td>
                        {% if row["judge"] == "NG_over_spec" %}
                            <td style="background-color: blue; color: white;">{{ row["judge"] }}</td>
                        {% elif row["judge"] == "NG_under_spec" %}
                            <td style="background-color: red; color: white;">{{ row["judge"] }}</td>
                        {% else %}
                            <td>{{ row["judge"] }}</td>
                        {% endif %}
                        <td>{{ row["lcl"] }}</td>
                        <td>{{ row["ucl"] }}</td>
                        <td>{{ row["download"]|safe }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="pagination">
            <button onclick="prevPage()">« 前のページ</button>
            <span id="page-info"></span>
            <button onclick="nextPage()">次のページ »</button>
        </div>
    </div>

    <script>
        let anomalyData = {{ table_data|tojson }};

        // 製品群 / 目的変数 のユニーク値を取得し、ドロップダウンへ
        let productSet = new Set();
        let testSet = new Set();
        anomalyData.forEach(row => {
            productSet.add(row.product);
            testSet.add(row.test);
        });
        let productList = Array.from(productSet);
        let testList = Array.from(testSet);

        let productSelect = document.getElementById("product-select");
        let testSelect = document.getElementById("test-select");

        productList.forEach(prod => {
            let opt = document.createElement("option");
            opt.value = prod;
            opt.textContent = prod;
            productSelect.appendChild(opt);
        });
        testList.forEach(ts => {
            let opt = document.createElement("option");
            opt.value = ts;
            opt.textContent = ts;
            testSelect.appendChild(opt);
        });

        function showGraph() {
            let selectedProduct = productSelect.value;
            let selectedTest = testSelect.value;
            let imgElem = document.getElementById("graph-display");

            let row = anomalyData.find(r => r.product === selectedProduct && r.test === selectedTest);
            if (row) {
                // row.graphpathが "/my_images/data_0/graph.png" などになっている想定
                imgElem.src = row.graphpath;
            } else {
                imgElem.src = "";
            }
        }

        // テーブルのフィルタ & ページング & ソート
        let rowsPerPage = 25;
        let currentPage = 1;
        let tableBody = document.querySelector("#result-table tbody");
        let allRows = Array.from(tableBody.getElementsByTagName("tr"));
        let filteredRows = [...allRows];

        function applyAllFilters() {
            let keyword = document.getElementById("filter-input").value.toLowerCase();
            filteredRows = allRows.filter(row => {
                return row.textContent.toLowerCase().includes(keyword);
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

        function sortTable(colIndex) {
            if (filteredRows.length === 0) return;
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

        updateTable();
    </script>
</body>
</html>
"""

#####################################
# Flaskルーティング
#####################################

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username] == password:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "ユーザーIDまたはパスワードが違います。"
    return render_template_string(login_template, error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    table_data = df_main.to_dict(orient="records")
    return render_template_string(dashboard_template, table_data=table_data)

@app.route("/anomaly/<int:anomaly_id>")
def anomaly_page(anomaly_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

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

    df_slice = df_result[df_result["DetectionType"] == anomaly_id].copy()
    df_slice["download"] = df_slice["download"].apply(
        lambda x: f'<a href="/download/{x}">ダウンロード</a>'
    )

    table_data = df_slice.to_dict(orient="records")
    return render_template_string(anomaly_template,
                                 anomaly_name=anomaly_name,
                                 table_data=table_data)

# ZIPファイルのダウンロード
@app.route("/download/<path:filename>")
def download_file(filename):
    src_dir = os.path.join(c.ROOT, r"data\files")
    return send_from_directory(directory=src_dir, path=filename, as_attachment=True)

# 画像ファイルを配信
@app.route("/my_images/<path:filename>")
def serve_my_images(filename):
    image_dir = os.path.join(c.ROOT, r"data\graphs")
    return send_from_directory(image_dir, filename)

if __name__ == "__main__":
    app.run(host="192.168.0.49", port=5000, debug=True)
