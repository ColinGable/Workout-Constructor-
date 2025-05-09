from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from gui import Ui_MainWindow
from datetime import *
import pandas as pd


class Logic(QMainWindow):
    def __init__(self) -> None:
        """Initialize the main logic window and connect UI components."""
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.exercises = pd.read_csv("Exercises.csv")
        if 'Muscle' not in self.exercises.columns or 'Name' not in self.exercises.columns:
            raise ValueError("The CSV file must contain 'Muscle' and 'Name' columns.")

        self.ui.button_enter_name.clicked.connect(self.name_entered)
        self.ui.Bodypart_select.currentTextChanged.connect(self.update_exercise_dropdown)
        self.ui.button_submit.clicked.connect(self.submit_exercise)
        self.ui.button_remove.clicked.connect(self.remove_selected_exercise)
        self.ui.button_Archive.clicked.connect(self.archive_current_workout)

        self.set_visibility(False)

    def populate_body_parts(self) -> None:
        """Populate the body part combo box with unique muscles from the exercise data."""
        self.ui.Bodypart_select.clear()
        muscles = sorted(self.exercises['Muscle'].dropna().unique())
        self.ui.Bodypart_select.addItems(muscles)

    def update_exercise_dropdown(self) -> None:
        """Update the exercise combo box based on selected body part."""
        selected_exercise = self.ui.Bodypart_select.currentText()
        self.ui.Exercise_select.clear()
        filtered = self.exercises[self.exercises['Muscle'] == selected_exercise]
        self.ui.Exercise_select.addItems(filtered['Name'].dropna().tolist())

    def set_visibility(self, visible: bool) -> None:
        """Show or hide workout-related widgets.

        :arg: visible True to show widgets, False to hide.
        """
        self.ui.Bodypart_select.setVisible(visible)
        self.ui.Exercise_select.setVisible(visible)
        self.ui.spinBox_reps.setVisible(visible)
        self.ui.spinBox_sets.setVisible(visible)
        self.ui.label_2.setVisible(visible)
        self.ui.label_3.setVisible(visible)
        self.ui.label_4.setVisible(visible)
        self.ui.label_5.setVisible(visible)
        self.ui.button_submit.setVisible(visible)
        self.ui.button_remove.setVisible(visible)
        self.ui.button_Archive.setVisible(visible)
        self.ui.workout_table.setVisible(visible)


    def name_entered(self) -> None:
        """Handle logic when a client name is entered and the Enter button is clicked."""
        client = self.get_client_name()
        if not client:
            self.ui.Error_message.setText("Please enter a valid name.")
            return

        self.ui.Error_message.setText("")
        self.set_visibility(True)
        self.populate_body_parts()
        self.show_current_workout()

    def get_client_name(self) -> str:
        """Get the client name from line edit.

        Returns: client name stripped and lowered.
        """
        return self.ui.lineEdit_name.text().strip().lower()

    def submit_exercise(self):
        """gets selected exercise data and put in into the table """
        client = self.get_client_name()

        if not client:
            return

        # Create a dictionary to store the new exercise
        new_exercise = {
            "Client": client,
            "Muscle": self.ui.Bodypart_select.currentText(),
            "Exercise": self.ui.Exercise_select.currentText(),
            "Reps": self.ui.spinBox_reps.value(),
            "Sets": self.ui.spinBox_sets.value()
        }


        file_name = f'{client}_workout.csv'

        # Try to open the file and read the old data
        try:
            old_data = pd.read_csv(file_name)
        except FileNotFoundError:
            # If the file doesn't exist, create an empty table with the correct columns
            old_data = pd.DataFrame(columns=["Client", "Muscle", "Exercise", "Reps", "Sets"])

        # Add the new exercise to the old data
        updated_data = pd.concat([old_data, pd.DataFrame([new_exercise])], ignore_index=True)

        # Save the updated data back to the same file
        updated_data.to_csv(file_name, index=False)

        # Show the updated table in the app
        self.show_current_workout()

    def show_current_workout(self) -> None:
        """Load and display the current workout entries for the selected client."""
        client = self.get_client_name()
        if not client:
            return

        try:
            client_exercises = pd.read_csv(f'{client}_workout.csv').fillna('')
        except FileNotFoundError:
            client_exercises = pd.DataFrame(columns=["Muscle", "Exercise", "Reps", "Sets"])

        self.display_workout_table(client_exercises)

    def display_workout_table(self, df: pd.DataFrame) -> None:
        """Render a given DataFrame in the workout table view.

        Args: pd.DataFrame Data to be shown on the table.
        """
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Muscle", "Exercise", "Reps", "Sets"])

        for index, row in df.iterrows():
            muscle_item = QStandardItem(str(row.get("Muscle", "")))
            exercise_item = QStandardItem(str(row.get("Exercise", "")))
            reps_item = QStandardItem(str(row.get("Reps", "")))
            sets_item = QStandardItem(str(row.get("Sets", "")))

            model.appendRow([muscle_item, exercise_item, reps_item, sets_item])

        self.ui.workout_table.setModel(model)

    def remove_selected_exercise(self) -> None:
        """Remove selected exercise entries from the table and update the CSV."""
        client = self.get_client_name()
        if not client:
            return

        try:
            all_exercises = pd.read_csv(f'{client}_workout.csv')
        except FileNotFoundError:
            return

        selected_rows = self.ui.workout_table.selectionModel().selectedRows() # Get the selected rows in the workout table

        if not selected_rows:
            return

        client_data = all_exercises[all_exercises["Client"].str.lower() == client].reset_index()
        original_indexes = [client_data.at[row.row(), "index"] for row in selected_rows]
        updated_data = all_exercises.drop(original_indexes)
        updated_data.to_csv(f'{client}_workout.csv', index=False)


        self.show_current_workout() # Refresh the table so the changes show up

    def archive_current_workout(self) -> None:
        """Archive all workout entries for the current client to a separate CSV.
        """
        client = self.get_client_name()
        if not client:
            return

        # Gets current time and formats it to save when user archives a workout
        time_stamp = datetime.now()
        formatted_stamp = time_stamp.strftime("%Y-%m-%d")
        workout_file = f'{client}_workout.csv'
        archive_file = f'{client}_archived{formatted_stamp}.csv'

        try:
            # Read all the client's workout data
            all_workouts = pd.read_csv(workout_file)
        except FileNotFoundError:
            return

        if all_workouts.empty:
            return

        try:
            archive_data = pd.read_csv(archive_file)
        except FileNotFoundError:
            archive_data = pd.DataFrame(columns=all_workouts.columns)

            # Combine existing archive with current workout
        updated_archive = pd.concat([archive_data, all_workouts], ignore_index=True)

        # Save updated archive
        updated_archive.to_csv(archive_file, index=False)

        # Clear the current workout file
        pd.DataFrame(columns=all_workouts.columns).to_csv(workout_file, index=False)

        # Clear the table in the GUI
        self.ui.workout_table.setModel(None)




