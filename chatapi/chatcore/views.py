from django.shortcuts import render, redirect
from django.urls import reverse
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
import openai
from .models import ChatGptBot, ChatGptApiKey, Profile
load_dotenv()
from django.contrib.auth import authenticate, login
from django.views.generic import CreateView, DeleteView, FormView
from .forms import SignUpForm, UserLoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAI
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import DirectoryLoader

# Create your views here.


def load_pdf(speciality):
    loader = DirectoryLoader('openapp/doc/' + speciality + '/', glob="**/*.pdf")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    return Chroma.from_documents(texts, embeddings, collection_name=speciality)


openai_api_key = ChatGptApiKey.objects.first().api_key


client = OpenAI(
    # This is the default and can be omitted
    api_key=openai_api_key
,
)


def pdfreaderprompt():
    prompt_template = """Blockchain, the foundation of Bitcoin, has received extensive attentions recently. Blockchain serves as an immutable ledger which allows transactions take place in a decentralized manner. Blockchain-based applications are springing up, covering numerous fields including financial services, reputation system and Internet of Things (IoT), and so on. However, there are still many challenges of blockchain technology such as scalability and security problems waiting to be overcome. The below contexr presents a comprehensive overview on blockchain technology.
{context}

Make sure you reply question only from the context.

{question}
"""
    return PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )


def CreateChatbot(speciality):
    vectorDB = load_pdf(speciality)
    llm = OpenAI(temperature=0, openai_api_key=openai_api_key)
    prompt = pdfreaderprompt()
    chain_type_kwargs = {
         "prompt": prompt
    }
    chatbot = RetrievalQA.from_chain_type(
         llm=llm, chain_type="stuff", retriever=vectorDB.as_retriever(),
         chain_type_kwargs=chain_type_kwargs
    )
    return chatbot


def index(request):
    #check if user is authenticated
    if request.user.is_authenticated:
        if request.method == 'POST':
            #get user input from the form
            user_input = request.POST.get('userInput')
            #clean input from any white spaces
            clean_user_input = str(user_input).strip()
            #send request with user's prompt
            try:
                speciality = Profile.objects.filter(user=request.user).first().speciality
                chatbot = CreateChatbot(speciality)
                query = clean_user_input
                response = chatbot.invoke(query)["result"]
                obj, created = ChatGptBot.objects.get_or_create(
                    user=request.user,
                    messageInput=clean_user_input,
                    bot_response=response,
                )
            except openai.APIConnectionError as e:
                #Handle connection error here
                messages.warning(request, f"Failed to connect to OpenAI API, check your internet connection")
            except openai.RateLimitError as e:
                #Handle rate limit error (we recommend using exponential backoff)
                messages.warning(request, f"You exceeded your current quota, please check your plan and billing details.")
                #messages.warning(request, f"If you are a developper change the API Key")

            return redirect(request.META['HTTP_REFERER'])
        else:
            #retrieve all messages belong to logged in user
            get_history = ChatGptBot.objects.filter(user=request.user)
            context = {'get_history': get_history}
            return render(request, 'index.html', context)
    else:
        return redirect("login")


class SignUp(CreateView):
    form_class = SignUpForm
    template_name = "users/register.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Get the user's username and password in order to automatically authenticate user after registration
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        # Authenticate the user and log him/her in
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.warning(self.request, f"{field}: {error}")
        return redirect(self.request.META['HTTP_REFERER'])

    def get_success_url(self):
        return reverse("main")


class LoginView(FormView):
    form_class = UserLoginForm
    template_name = "login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Get the user's username and password and authenticate
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        # Authenticate the user and log him/her in
        user = authenticate(username=username, password=password)
        login(self.request, user)
        #messages.success(self.request, "You are logged in")
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.warning(self.request, f"{error}")
        return redirect(self.request.META['HTTP_REFERER'])

    def get_success_url(self):
        return reverse("main")


@login_required
def DeleteHistory(request):
    chat_gpt_objs = ChatGptBot.objects.filter(user=request.user)
    chat_gpt_objs.delete()
    #messages.success(request, "All messages have been deleted")
    return redirect(request.META['HTTP_REFERER'])


def logout_view(request):
    logout(request)
    #messages.success(request, "Succesfully logged out")
    return redirect("main")
