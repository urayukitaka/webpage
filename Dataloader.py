import yfinance as yf
import pandas as pd
import json

# -------------------------------------------------
# parameters
# -------------------------------------------------
exe_tble_path = r"C:\Users\yktkk\Desktop\DS_practice\programing\WebPage\datadash\dataset\execute_table\execute_tble.xlsx"


# -------------------------------------------------
# functions
# -------------------------------------------------
# load json file
def load_json(file_path):
    """
    指定されたJSONファイルを読み込み、辞書オブジェクトとして返す。

    :param file_path: 読み込むJSONファイルのパス
    :return: JSONデータを辞書として返す
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
    except json.JSONDecodeError:
        print(f"エラー: ファイル '{file_path}' のJSONフォーマットが正しくありません。")
    except Exception as e:
        print(f"エラー: {e}")

# loader, execute list
class DataExe:

    def __init__(self,
                 exe_tble_path:str=exe_tble_path)->None:

        # file
        self.exe_tble_path = exe_tble_path
        # load
        self.__loadfiles()

    def __loadfiles(self,):
        # exe table
        self.exe_tble = pd.read_excel(self.exe_tble_path)
        # preprocessing
        self.exe_tble["更新日"] = pd.to_datetime(self.exe_tble["更新日"])
        self.exe_tble.sort_values(by="更新日", inplace=True)
        # latest flg
        flg = {}
        for k in self.exe_tble["異常検知種"].unique():
            # mindate
            mindate = self.exe_tble[self.exe_tble["異常検知種"]==k]["更新日"].min()
            flg[k] = {str(mindate):"●"}
        latest = []
        for k, d in zip(self.exe_tble["異常検知種"], self.exe_tble["更新日"]):
            try:
                latest.append(flg[k][str(d)])
            except:
                latest.append(None)
        self.exe_tble["latest"] = latest
        self.exe_tble.reset_index(drop=True)

        # slice len 20
        if len(self.exe_tble)>20:
            self.exe_tble = self.exe_tble.iloc[:20,:]
        print("")

# loader, Nikkei
class Data:
    def __init__(self,
                 nikkei_list_file_path:str,
                 translation_dict_path:str)->None:
        # files
        self.nikkei_path = nikkei_list_file_path # csv file
        self.trans_path = translation_dict_path # json file
        self.__loadfiles()

        # company class
        self.com = None

    def __loadfiles(self):
        # nikkei list
        self.nikkei = pd.read_csv(self.nikkei_path, encoding="CP932").sort_values(by="銘柄名")
        self.nikkei_items = self.nikkei.set_index("銘柄名").to_dict("index")
        # transition dict
        self.trans = load_json(self.trans_path)

    def set_company(self,
                    code:str,
                    initialize:bool=False):
        # set
        code = str(code) + ".T"

        if initialize:
            del self.com
        else:
            self.com = yf.Ticker(code)

    def getinfo(self):
        return self.com.info

    def gethistory(self,
                   period:int):
        period = f"{period}d"
        return self.com.history(period).sort_index(ascending=False)

# debub
if __name__ == "__main__":
    DataExe(exe_tble_path=exe_tble_path)
