import AppConstants from '../constants/app-constants';
import _ from 'lodash';

//TODO: need to cascade & choice rules when needed
var RULES = {},
    SURVEY_RULES = [];

function setup () {
  SURVEY_RULES.push(questionLabelIsMandatory);
  RULES.SurveyRules = SURVEY_RULES;
}

//TODO Extract rule into separate file when needed
var questionLabelIsMandatory = function (question) {
  let errors = {};

  if(!question.label) {
    errors[question.name] = errors[question.name] || {};
    errors[question.name] = {
      label: AppConstants.CommonErrorMessages.REQUIRED_ERROR_MESSAGE
    };
  }

  return errors;
};

var validateQuestionnaire = function (questionnaire) {
  let errors = [];
  _.forEach(questionnaire.survey, function (question) {
    errrors = _.concate(errors, validateQuestion(question));
  });
  return errors;
};

var validateQuestion = function (question) {
  let errors = [];
  _.forEach(RULES.SurveyRules, function (rule) {
      errors.push(rule(question));
    });
  return errors;
};

setup();

module.exports = {
                    validateQuestion : validateQuestion,
                    validateQuestionnaire : validateQuestionnaire
                 };
