import streamlit as st
import copy
import pandas as pd

# ---------------- Batsman Class ----------------
class Batsman:
    def __init__(self, name: str):
        self.name = name
        self.runs = 0
        self.balls = 0
        self.fours = 0
        self.sixes = 0
        self.dot_balls = 0
        self.out = False

    def add_runs(self, runs: int):
        self.runs += runs
        self.balls += 1
        if runs == 0:
            self.dot_balls += 1
        elif runs == 4:
            self.fours += 1
        elif runs == 6:
            self.sixes += 1

    def mark_out(self):
        self.out = True

    def get_strike_rate(self) -> float:
        return round((self.runs / self.balls) * 100, 2) if self.balls > 0 else 0.0

    def boundary_percentage(self) -> float:
        boundary_runs = (self.fours * 4) + (self.sixes * 6)
        return round((boundary_runs / self.runs) * 100, 2) if self.runs > 0 else 0.0


# ---------------- TeamBatting Class ----------------
class TeamBatting:
    def __init__(self, name: str, players: list[str], max_overs: int):
        self.name = name
        self.players = [Batsman(p) for p in players]
        self.max_overs = max_overs
        self.total_runs = 0
        self.wickets = 0
        self.extras = {"wide": 0, "noball": 0, "bye": 0, "legbye": 0}
        self.balls_bowled = 0
        self.current_batsmen = [self.players[0], self.players[1]]
        self.next_batsman_index = 2
        self.free_hit = False

    def legal_overs(self):
        return f"{self.balls_bowled // 6}.{self.balls_bowled % 6}"

    def add_runs_from_bat(self, runs: int):
        striker = self.current_batsmen[0]
        striker.add_runs(runs)
        self.total_runs += runs
        self.balls_bowled += 1
        if runs % 2 == 1:
            self.current_batsmen.reverse()
        if self.balls_bowled % 6 == 0:
            self.current_batsmen.reverse()
        self.free_hit = False

    def add_extras(self, runs: int, extra_type: str):
        if extra_type == "wide":
            self.total_runs += runs
            self.extras["wide"] += runs
            # wides are not legal deliveries
            if runs % 2 == 0:
                self.current_batsmen.reverse()

        elif extra_type == "noball":
            self.total_runs += 1
            self.extras["noball"] += 1
            self.free_hit = True
            if runs > 1:
                bat_runs = runs - 1
                striker = self.current_batsmen[0]
                striker.add_runs(bat_runs)
                self.total_runs += bat_runs
                if bat_runs % 2 == 1:
                    self.current_batsmen.reverse()

        elif extra_type in ["bye", "legbye"]:
            self.total_runs += runs
            self.extras[extra_type] += runs
            self.balls_bowled += 1
            if runs % 2 == 1:
                self.current_batsmen.reverse()
            if self.balls_bowled % 6 == 0:
                self.current_batsmen.reverse()
            self.free_hit = False

    def add_wicket(self):
        if self.free_hit:
            st.info("❌ Wicket on Free Hit! Not counted.")
            self.balls_bowled += 1
            if self.balls_bowled % 6 == 0:
                self.current_batsmen.reverse()
            self.free_hit = False
            return
        striker = self.current_batsmen[0]
        striker.mark_out()
        self.wickets += 1
        self.balls_bowled += 1
        if self.next_batsman_index < len(self.players):
            self.current_batsmen[0] = self.players[self.next_batsman_index]
            self.next_batsman_index += 1
        if self.balls_bowled % 6 == 0:
            self.current_batsmen.reverse()
        self.free_hit = False

    def is_innings_over(self) -> bool:
        max_balls = self.max_overs * 6
        all_out = self.wickets >= (len(self.players) - 1)
        overs_done = self.balls_bowled >= max_balls
        return all_out or overs_done

    def score_summary(self):
        return {
            "score": f"{self.total_runs}/{self.wickets}",
            "overs": self.legal_overs(),
            "extras": self.extras,
            "batsmen": [f"{p.name}: {p.runs}({p.balls})" for p in self.players],
        }


# ---------------- Streamlit App ----------------
st.set_page_config(page_title="Cricket Score App", layout="wide")
st.title("🏏 Cricket Scoring App")

# Initialize session state keys
if "team" not in st.session_state:
    st.session_state.team = None
if "action" not in st.session_state:
    st.session_state.action = None
if "awaiting_extra" not in st.session_state:
    st.session_state.awaiting_extra = None
if "history" not in st.session_state:
    st.session_state.history = []


def save_state():
    """Push a deep copy of current team to history for Undo."""
    if st.session_state.team is not None:
        st.session_state.history.append(copy.deepcopy(st.session_state.team))


def undo_state():
    """Restore last saved state (if any)."""
    if st.session_state.history:
        st.session_state.team = st.session_state.history.pop()
        return True
    else:
        st.warning("Nothing to undo.")
        return False


# ---------------- Setup Match ----------------
if not st.session_state.team:
    st.subheader("Setup Match")
    team_name = st.text_input("Enter Team Name:")
    num_players = st.number_input("Enter number of players:", min_value=2, max_value=11, value=2)
    max_overs = st.number_input("Enter maximum overs:", min_value=1, max_value=50, value=2)
    players = []
    for i in range(num_players):
        players.append(st.text_input(f"Enter name of player {i+1}:", key=f"p{i}"))

    if st.button("Start Match"):
        if team_name.strip() and all(p.strip() for p in players):
            st.session_state.team = TeamBatting(team_name.strip(), players, int(max_overs))
            st.session_state.action = None
            st.session_state.awaiting_extra = None
            st.session_state.history = []
            st.rerun()
        else:
            st.warning("Please enter a team name and all player names to start.")

# ---------------- Match In Progress ----------------
else:
    team: TeamBatting = st.session_state.team
    innings_over = team.is_innings_over()  # ✅ check here once

    st.subheader(f"{team.name} Innings")
    st.markdown(f"**Score:** {team.total_runs}/{team.wickets}   |   **Overs:** {team.legal_overs()}")
    st.markdown(
        f"**On strike:** {team.current_batsmen[0].name} {'(FREE HIT!)' if team.free_hit else ''}"
    )

    # Live extras summary
    extras_total = sum(team.extras.values())
    st.markdown(
        f"**Extras:** {extras_total}  "
        f"(Wides: {team.extras['wide']}, No-balls: {team.extras['noball']}, "
        f"Byes: {team.extras['bye']}, Leg-byes: {team.extras['legbye']})"
    )

    # Undo only if not over
    col_undo, _ = st.columns([1, 4])
    with col_undo:
        if not innings_over and st.button("↩️ Undo Last Ball"):
            restored = undo_state()
            if restored:
                st.rerun()

    # ✅ Disable scoring if innings is over
    if not innings_over:
        # Runs buttons
        st.markdown("### Runs from Bat")
        cols = st.columns(6)
        run_values = [0, 1, 2, 3, 4, 6]
        for i, run in enumerate(run_values):
            if cols[i].button(str(run)):
                save_state()
                st.session_state.action = ("runs", run)

        # Extras & Wicket buttons
        st.markdown("### Extras & Wicket")
        ex_cols = st.columns(5)
        if ex_cols[0].button("Wide"):
            st.session_state.awaiting_extra = "wide"
        if ex_cols[1].button("No-ball"):
            st.session_state.awaiting_extra = "noball"
        if ex_cols[2].button("Bye"):
            st.session_state.awaiting_extra = "bye"
        if ex_cols[3].button("Leg-bye"):
            st.session_state.awaiting_extra = "legbye"
        if ex_cols[4].button("Wicket"):
            save_state()
            st.session_state.action = ("wicket", None)

        # If an extra type is selected, ask for runs
        if st.session_state.awaiting_extra:
            etype = st.session_state.awaiting_extra
            st.markdown(f"#### Enter runs for {etype.capitalize()}")
            if etype == "wide":
                runs = st.number_input(
                    "Total runs for wide (default 1):", min_value=1, max_value=10, value=1, step=1
                )
                if st.button("Confirm Wide"):
                    save_state()
                    st.session_state.action = ("extra", (etype, runs))
                    st.session_state.awaiting_extra = None
                    st.rerun()

            elif etype == "noball":
                bat_runs = st.number_input(
                    "Runs off the bat on the no-ball (0–6):", min_value=0, max_value=6, value=0, step=1
                )
                if st.button("Confirm No-ball"):
                    save_state()
                    st.session_state.action = ("extra", (etype, 1 + bat_runs))
                    st.session_state.awaiting_extra = None
                    st.rerun()

            elif etype in ["bye", "legbye"]:
                runs = st.number_input(
                    f"Runs for {etype.capitalize()} (legal delivery):", min_value=1, max_value=10, value=1, step=1
                )
                if st.button(f"Confirm {etype.capitalize()}"):
                    save_state()
                    st.session_state.action = ("extra", (etype, runs))
                    st.session_state.awaiting_extra = None
                    st.rerun()

        # Execute queued action
        if st.session_state.action:
            act, val = st.session_state.action
            if act == "runs":
                team.add_runs_from_bat(val)
            elif act == "wicket":
                team.add_wicket()
            elif act == "extra":
                etype, runs = val
                team.add_extras(runs, etype)
            st.session_state.action = None
            st.rerun()

    # Batsman stats table
    st.markdown("### Batsman Stats")
    batsmen_rows = []
    for p in team.players:
        batsmen_rows.append(
            {
                "Name": p.name,
                "Runs": p.runs,
                "Balls": p.balls,
                "4s": p.fours,
                "6s": p.sixes,
                "Dots": p.dot_balls,
                "SR": p.get_strike_rate(),
                "Boundary%": p.boundary_percentage(),
                "Status": "Out" if p.out else "Not Out",
            }
        )
    st.dataframe(pd.DataFrame(batsmen_rows), use_container_width=True)

    # Final summary
    if innings_over:
        st.success("🏁 Innings Over!")
        summary = team.score_summary()
        st.write(f"**Final Score:** {summary['score']} in {summary['overs']} overs")
        st.write("**Extras breakdown:**", summary["extras"])

        # Button to start a new match
        if st.button("🔄 Start New Match"):
            st.session_state.team = None
            st.session_state.history = []
            st.session_state.action = None
            st.session_state.awaiting_extra = None
            st.rerun()
