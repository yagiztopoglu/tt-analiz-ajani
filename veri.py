"""StatsBomb açık verisinden 2022 Dünya Kupası finalini (Arjantin–Fransa) çeker."""
import warnings

import pandas as pd
from statsbombpy import sb

warnings.filterwarnings("ignore")  # statsbombpy'nin "credentials" uyarısını gizle

# 1) 2022 Dünya Kupası'nı yarışma listesinden bul
comps = sb.competitions()
wc = comps[(comps["competition_name"] == "FIFA World Cup") & (comps["season_name"] == "2022")].iloc[0]

# 2) Final maçını bul
matches = sb.matches(competition_id=wc["competition_id"], season_id=wc["season_id"])
final = matches[matches["competition_stage"] == "Final"].iloc[0]
print(f"Maç: {final['home_team']} {final['home_score']} - {final['away_score']} {final['away_team']} "
      f"({final['match_date']}, match_id={final['match_id']})\n")

# 3) Olayları pandas DataFrame olarak çek
events: pd.DataFrame = sb.events(match_id=final["match_id"])
events = events.sort_values(["index"]).reset_index(drop=True)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 12)

print(f"Toplam olay: {len(events)}, sütun sayısı: {events.shape[1]}\n")
print("İlk 10 satır:")
print(events[["index", "period", "minute", "second", "type", "team", "player", "location"]].head(10))

print("\nOlay tiplerine göre sayılar:")
print(events["type"].value_counts().to_string())
