import React from 'react';
import QuestionnaireStore from '../store/questionnaire-store';
import AppConstants from '../constants/app-constants';
import Question from './question';
import Paper from 'material-ui/lib/paper';
import AppBar from 'material-ui/lib/app-bar';

import IconButton from 'material-ui/lib/icon-button';
import ActionHome from 'material-ui/lib/svg-icons/action/home';
import RaisedButton from 'material-ui/lib/raised-button';
import FloatingActionButton from 'material-ui/lib/floating-action-button';
import ContentAdd from 'material-ui/lib/svg-icons/content/add';
import Card from 'material-ui/lib/card/card';

// var CardActions = require('material-ui/lib/card/card-actions');
import CardText from 'material-ui/lib/card/card-text';
import SelectField from 'material-ui/lib/select-field';
import QuestionnaireActions from '../actions/questionnaire-actions';
import MenuItem from 'material-ui/lib/menus/menu-item';
import _ from 'lodash';
import CircularProgress from 'material-ui/lib/circular-progress';

const style = {
	addButtonContainer: {
		position: 'relative',
    bottom: '22px',
    right: '20px',
    float: 'right'
	},
	appBar: {
		backgroundColor: '#E8EFF6'
	},
	saveButton: {
		backgroundColor: 'red'
	}
};
//
// let getAllQuestions = function(questionnaire_id){
// 	return {
// 		questions: QuestionnaireStore.getAllQuestions(questionnaire_id)
// 	};
// };

export default class QuestionnaireList extends React.Component {
	constructor(props){
		super(props);
		this.state = {
				questionnaire_id:props.questionnaire_id
				// questions: getAllQuestions(props.questionnaire_id)
		}
		this.onQuestionChange = this.onQuestionChange.bind(this);
		this.saveQuestionnaire = this.saveQuestionnaire.bind(this);
	}

	componentDidMount(){
		let url = AppConstants.QuestionnaireUrl + this.state.questionnaire_id + '/';
		var self = this;
		this.serverRequest = $.ajax({
				url: url,
				dataType: 'json',
				success: function (result) {
		      self.setState({
		        questionnaire: result.questionnaire
		      });
				}
			});
	}

	componentWillMount(){
		QuestionnaireStore.addChangeListener(this._onChange);
	}

	componentWillUnmount() {
		this.serverRequest.abort();
	}

	_onChange(){
		this.setState({questions:getAllQuestions(this.state.id)})
	}

	onQuestionChange(updated_question){
		let current_question_index = _.findIndex(
																					this.state.questionnaire.survey,
																					{name:updated_question.name});
		let questions = this.state.questionnaire.survey;
		questions[current_question_index] = updated_question;
		this.setState({questions: questions});
	}

	getQuestionTypeMenuItems() {
    var question_type_menu_items = [];
    for (var key in AppConstants.QuestionTypesDropdown){
      question_type_menu_items.push(
        <MenuItem
						value={AppConstants.QuestionTypesDropdown[key]}
						primaryText={AppConstants.QuestionTypesDropdown[key]} />
      );
    }
    return question_type_menu_items;
  }

	saveQuestionnaire(event) {
		event.preventDefault();

		//TODO
		// if (!this.questionFormIsValid()) {
		// 	return;
		// }

    //TODO - id is not longer meaningful.,
		// if (this.state.question.id) {
		// 	QuestionActions.updateQuestion(this.state.question);
		// } else {
		// 	QuestionActions.createQuestion(this.state.question);
		// }

		let status = QuestionnaireActions.saveQuestionnaire(
											this.state.questionnaire_id,this.state.questionnaire.survey);
		//TODO: should update dirty flag to false

		// if (status) {
		// 	Toastr.success('Questionnaire saved successfully');
		// }else{
		// 	Toastr.error('Unable to save questionnaire');
		// }
	}


	render(){
		if (!this.state.questionnaire){
			return <CircularProgress />
		}
		var questions = this.state.questionnaire.survey;
    var displayQuestions = [];

    for (var key in questions) {
			if (AppConstants.QuestionTypeSupport[questions[key].type]) {
				displayQuestions.push(
					<Question
							key={questions[key].name}
							question={questions[key]}
							onChange={this.onQuestionChange}/>
				);
			}
    }

		return (
			<div>
      <Paper zDepth={3} >
        <AppBar
					showMenuIconButton={false}
          title={<span>Questionnaire Builder</span>}
          iconElementRight={<RaisedButton label="Save" style={style.saveButton} onMouseDown={this.saveQuestionnaire} />}
          />
					{displayQuestions}

          <Card expanded={this.state.expandNewQuestionType}>
          <CardText expandable={true}>
                <SelectField
                          floatingLabelText="Question Type"
                        >
                          {this.getQuestionTypeMenuItems()}
                  </SelectField>
            </CardText>
          </Card>
          <div style={style.addButtonContainer}>
            <FloatingActionButton onMouseDown={this.handleAddButtonClick}>
              <ContentAdd />
            </FloatingActionButton>
          </div>
      </Paper>
      </div>
				);
	}
}
