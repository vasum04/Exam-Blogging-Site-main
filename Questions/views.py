from django.shortcuts import render, HttpResponse, Http404, get_object_or_404, HttpResponseRedirect, redirect
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


from django.conf import settings

from .models import *

# Create your views here.
media_url = settings.MEDIA_URL
static = settings.STATIC_URL
site_info = settings.SITE_INFO
LOGIN_URL = settings.LOGIN_URL
LOGOUT_URL = settings.LOGOUT_URL

def ViewCategoryPage(request, category):
    passing_dictionary = {
        'media_url': media_url,
    }
    passing_dictionary['category'] = category
    try:
        category_instance = QuestionCategory.objects.all().get(category = category)
        questions_obj = Questions.objects.all().filter(category = category_instance)
        passing_dictionary['questions'] = questions_obj
    except:
        passing_dictionary ['categoryNotFound'] = True
        passing_dictionary ['errors'] = 'There is some error with your request or with the site. Sorry for the inconvenience.'
    return render( request, 'core/template-view-category.html', passing_dictionary )

def ViewAllCategories(request):
    passing_dictionary = {
        'media_url': media_url,
    }
    category_question_number = {}
    categories_object = QuestionCategory.objects.all()
    for category in categories_object:
        temp_obj = Questions.objects.all().filter(category = category)
        category_question_number [ category.category ] = len(temp_obj)
    passing_dictionary['categories'] = category_question_number
    return render( request, 'core/template-all-categories.html', passing_dictionary )
    

@login_required( login_url= LOGIN_URL)
def QuestionsActions(request, action, param = None):
    passing_dictionary = {
        'media_url': media_url,
    }
    if action == "add" or action == "edit":
        try:
            categories_object = QuestionCategory.objects.all()
        except QuestionCategory.DoesNotExist:
            categories_object = {}
        passing_dictionary['categories'] = categories_object

        if action == "edit" and param is not None:
            try:
                question_object = Questions.objects.get(id = param)
                if ( question_object.author.id is not request.user.id ):
                    #unauthorized person should not access
                    raise Http404()
                else:
                    #the question can be edited
                    if request.method == 'POST':
                        # data received for the question
                        question_category = request.POST["category"]
                        
                        try:
                            category_instance = QuestionCategory.objects.get(category = question_category)
                        except QuestionCategory.DoesNotExist:
                            QuestionCategory.objects.create(category = question_category)
                            try:
                                category_instance = QuestionCategory.objects.get(category = question_category)
                            except QuestionCategory.DoesNotExist: 
                                return HttpResponse ('There might be some error with the site.')

                        question_obj = Questions.objects.get( 
                                                id = param
                                            )    
                        question_obj.question = request.POST["question"]                                                 
                        question_obj.category = category_instance
                        question_obj.slug = request.POST["slug"]

                        if( 'anonymous' in request.POST and request.POST['anonymous'] != False):
                            question_obj.anonymous = True
                        else:
                            question_obj.anonymous = False

                        question_obj.save()
                        redir_url =  '/'+ request.POST['slug'] 
                    
                        return redirect ( redir_url )
                    else:
                        # if no form was posted then
                        passing_dictionary ['question'] = question_object                    
                    
            except Questions.DoesNotExist:
                raise Http404()
        if action == "add" and request.method == "POST":
            question_category = request.POST["category"]
            try:
                category_instance = QuestionCategory.objects.get ( category = question_category )
            except QuestionCategory.DoesNotExist:
                QuestionCategory.objects.create(category = question_category)
                try:
                    category_instance = QuestionCategory.objects.get (category = question_category)
                except QuestionCategory.DoesNotExist: 
                    return HttpResponse ('There might be some error with the site.')
            
            if( 'anonymous' in request.POST and request.POST['anonymous'] != False):
                anonymous = True
            else:
                anonymous = False
                
            new_question_obj = Questions.objects.create( 
                                    question = request.POST["question"], 
                                    author = request.user,
                                    category = category_instance,
                                    slug = request.POST["slug"],
                                    anonymous = anonymous
                                 )    
            #redir_url =  request.get_host() +'/'+ request.POST['slug'] 
            redir_url =  '/'+ request.POST['slug'] 
            
            return redirect ( redir_url )
        passing_dictionary ['action'] = action                
        return render( request, 'core/template-mod-question.html', passing_dictionary )
    if action == "delete" and param is not None:
        if '@' in param:
            param = param.split('@')
            delete_type = param[0].lower()
            delete_id = param[1]
            if delete_type == 'question':
                obj = Questions.objects.get(id = delete_id)
                request.session['dashMessage'] = 'Question deletion Success!' # message
                obj.delete()
                return HttpResponseRedirect('/dashboard')
            elif delete_type == 'answer':
                obj = Answers.objects.get(id = delete_id)
                obj.delete()
                if 'next' in request.GET:
                    return redirect( request.GET['next'] , status =302 )
                return HttpResponseRedirect('/dashboard')
            elif delete_type == 'category':
                obj = Answers.objects.get(id = delete_id)
                obj.delete()
                return HttpResponseRedirect('/dashboard')            
            else:
                raise Http404()

    else: 
        raise Http404()

def ViewQuestion(request, question):
    passing_dictionary = {
        'media_url': media_url,
    }
    if request.method == 'POST':
        # if something is posted e.g. answer!
        new_answer = request.POST['new_answer']
        question_id = request.POST['ques_id']
        current_user = request.user
            
        if( 'anonymous' in request.POST and request.POST['anonymous'] != False):
            anonymous = True
        else:
            anonymous = False

        if new_answer is not None and question_id is not None and current_user is not None:
            question_instance = Questions.objects.get( id = question_id )
            Answers.objects.create( question = question_instance, 
                                    author = current_user,
                                    answer = new_answer,
                                    anonymous = anonymous,
                                 )
        else:
            return HttpResponse("There is some error with your answer. Try Again")

    try:
#        question_object = Questions.object.get(question = question)
        question_object = Questions.objects.get(slug = question)
        answers_object = {}
        categories_object = {}
        upvoters = question_object.upvoters
        upvoters_list = upvoters.split(',')
        if str(request.user.id) in upvoters_list:
            passing_dictionary['question_upvoted'] = True
        else:
            passing_dictionary['question_upvoted'] = False

        try:
            answers_object = Answers.objects.filter(question = question_object).order_by('-isBestAnswer')
            answer_upvoted_dict = {}
            for answer in answers_object:
                if answer.upvote > 0 and str(request.user.id) in answer.upvoters.split(','):
                    answer_upvoted_dict [ answer.id ] = True                    
            passing_dictionary [ 'upvoted_answers' ] = answer_upvoted_dict    

        except Answers.DoesNotExist:
            answers_object = {}
        passing_dictionary['question'] = question_object
        passing_dictionary['answers'] = answers_object

    except Questions.DoesNotExist:
        raise Http404
    
    # print(passing_dictionary)
    return render( request, 'core/template-view-question.html', passing_dictionary)

#@login_required( login_url= LOGIN_URL)
def DoUpvote(request):
    outputJsonDict = {}
    if request.user.id is not None:
        if 'type' in request.GET and request.GET['type'] != "":
            up_type = request.GET['type'].lower()
            if 'id' not in request.GET or request.GET['type'] == "" or request.GET['id'] == '':
                outputJsonDict['code'] = 'error'
                outputJsonDict['action'] = 'upvote'
                outputJsonDict['message'] = 'No ID received. Try Again'
                outputJsonDict['data'] = {}
                return JsonResponse(outputJsonDict)
            
            upvote_id = int(request.GET['id'])
            if up_type == "question":
                current_user = request.user.id
                question_object = get_object_or_404(Questions, id=upvote_id)
                upvote = question_object.upvote
                upvoters_list = question_object.upvoters.split(',')

                if str(current_user) in upvoters_list:
                    upvote -= 1
                    question_object.upvote = upvote
                    
                    upvoters_list.remove( str(current_user) )
                    question_object.upvoters =  ','.join(upvoters_list)
                    
                    question_object.save()
                    
                    outputJsonDict['code'] = 'success'
                    outputJsonDict['action'] = 'downvote'
                    outputJsonDict['message'] = 'Downvote Success'
                    outputJsonDict['data'] = { 'upvotes' : upvote }
                    return JsonResponse(outputJsonDict)
                else:
                    upvote += 1
                    question_object.upvote = upvote
                    question_object.upvoters += str(current_user)+","
                    question_object.save()
                    outputJsonDict['code'] = 'success'
                    outputJsonDict['action'] = 'upvote'
                    outputJsonDict['message'] = 'Upvote Success'
                    outputJsonDict['data'] = { 'upvotes' : upvote }
                    return JsonResponse(outputJsonDict)

            elif up_type == "answer":
                answer_object = get_object_or_404(Answers, id=upvote_id)
                current_user = request.user.id

                upvote = answer_object.upvote
                upvoters_list = answer_object.upvoters.split(',')

                if str(current_user) in upvoters_list:
                    upvote -= 1
                    answer_object.upvote = upvote
                    
                    upvoters_list.remove( str(current_user) )
                    answer_object.upvoters =  ','.join(upvoters_list)
                    
                    answer_object.save()
                    
                    outputJsonDict['code'] = 'success'
                    outputJsonDict['action'] = 'downvote'
                    outputJsonDict['message'] = 'Downvote Success'
                    outputJsonDict['data'] = { 'upvotes' : upvote }
                    return JsonResponse(outputJsonDict)
                    
                else:
                    upvote += 1
                    answer_object.upvote = upvote
                    answer_object.upvoters += str(current_user)+","
                    answer_object.save()
                    outputJsonDict['code'] = 'success'
                    outputJsonDict['action'] = 'upvote'
                    outputJsonDict['message'] = 'Upvote Success'
                    outputJsonDict['data'] = { 'upvotes' : upvote }
                    return JsonResponse(outputJsonDict)

            else:
                outputJsonDict['code'] = 'error'
                outputJsonDict['action'] = 'upvote'
                outputJsonDict['message'] = 'Invalid Type. Try Again.'
                outputJsonDict['data'] = {}
                return JsonResponse(outputJsonDict)

        else:
            outputJsonDict['code'] = 'error'
            outputJsonDict['action'] = 'upvote'
            outputJsonDict['message'] = 'Invalid or No Params. Try Again.'
            outputJsonDict['data'] = {}
            return JsonResponse(outputJsonDict)
    else:
        outputJsonDict['code'] = 'invalid_user'
        outputJsonDict['action'] = 'upvote'
        outputJsonDict['message'] = 'Invalid User'
        outputJsonDict['data'] = {}
        return JsonResponse(outputJsonDict)

@csrf_exempt
def CheckSlugWithAjax(request):
    outputJsonDict = {}
    if request.method == 'POST' and request.POST ['slug'] is not None:
        slug = request.POST ['slug']
        outputJsonDict['code'] = 'error'
        outputJsonDict['slug'] = slug
        
        try:
            Questions.objects.get( slug = slug )
            outputJsonDict['code'] = True
            return JsonResponse(outputJsonDict)

        except Questions.DoesNotExist:
            outputJsonDict['code'] = False
            return JsonResponse(outputJsonDict)
    else:
        outputJsonDict['code'] = 'error'
        return JsonResponse(outputJsonDict)

@csrf_exempt
def AddCategoryWithAjax(request):
    outputJsonDict = {}
    if request.method == 'POST' and request.POST ['category'] is not None:
        category = request.POST ['category']
        
        outputJsonDict['category'] = category
        try:
            QuestionCategory.objects.get(category = category)
            outputJsonDict['code'] = 'error'
            outputJsonDict['message'] = 'Category already exists.'
            return JsonResponse (outputJsonDict)
        except QuestionCategory.DoesNotExist:
            try:
                QuestionCategory.objects.create(category = category)
                outputJsonDict['code'] = 'success'
                outputJsonDict['message'] = 'Added Category: '+category
                return JsonResponse (outputJsonDict)
            except:
                outputJsonDict['code'] = 'error'
                outputJsonDict['message'] = 'There was some error in adding the category'
                return JsonResponse (outputJsonDict)
    else:
        outputJsonDict['code'] = 'error'
        outputJsonDict['message'] = 'Invalid or No Params.'
        return JsonResponse(outputJsonDict)

@csrf_exempt
def AjaxHandler(request):
    data = {}
    if 'action' in request.GET:
        action = request.GET['action']
        if action == 'editAnswer' and 'ansId' in request.POST:
            # time to edit the answer
            ansId = request.POST['ansId']
            print (ansId)
            data ['id'] = ansId
            answer_object = Answers.objects.all().get(id=ansId)
            answer_object.answer = request.POST['answer']
            if 'anonymous' in request.POST and request.POST['anonymous'] == 'true' or request.POST['anonymous'] == True:
                now_anonymous = True
            else:
                now_anonymous = False                
            
            answer_object.anonymous = now_anonymous
            answer_object.save()
            data['code'] = 'success'
            data ['new_answer'] = request.POST['answer']
            data ['anonymous'] = now_anonymous

        return JsonResponse(data)
    else:
        data['code'] = 'error'
        data['message'] = 'No Action in Params'
    return JsonResponse(data)

def SearchHandler(request):
    passing_dictionary = {}
    if 'q' in request.GET and request.GET['q'] != "":
        query = request.GET['q']
        passing_dictionary ['query'] = query
        questions_results = Questions.objects.filter(question__icontains=query)
        passing_dictionary ['questions_results'] = questions_results
        
        answers_results = Answers.objects.filter(answer__icontains=query)
        passing_dictionary ['answers_results'] = answers_results
        
    else:
        passing_dictionary['searchNotDone'] = True
    return render( request, 'core/template-search.html', passing_dictionary)


def BestAnswerHandler(request):
    if request.method == 'GET' and 'id' in request.GET:
        flag = False

        ansId = request.GET['id']
        ans_obj = get_object_or_404(Answers, id=ansId)
        ques_obj = Questions.objects.get(id = ans_obj.question.id)

        if ques_obj.author.id != request.user.id:
            raise Http404()

        if ans_obj.isBestAnswer:
            flag = True

        all_ans = Answers.objects.filter(question = ques_obj)
        for temp_answer in all_ans:
            if temp_answer.isBestAnswer:
                temp_answer.isBestAnswer = False
                temp_answer.save()

        if not flag:
            ans_obj.isBestAnswer = True
            ans_obj.save()

        return HttpResponseRedirect( '/'+ques_obj.slug )
    raise Http404()