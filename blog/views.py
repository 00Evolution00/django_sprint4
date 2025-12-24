from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserEditForm, UserRegistrationForm
from .utils import annotate_comment_count, paginate

User = get_user_model()


def index(request):
    post_list = Post.objects.select_related(
        'author', 'location', 'category'
    ).filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True,
    )
    post_list = annotate_comment_count(post_list)
    page_obj = paginate(request, post_list)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_published=True)
    post_list = Post.objects.select_related(
        'author', 'location', 'category'
    ).filter(
        category=category,
        is_published=True,
        pub_date__lte=now()
    )
    post_list = annotate_comment_count(post_list)
    page_obj = paginate(request, post_list)
    return render(request, 'blog/category.html', {'category': category, 'page_obj': page_obj})


def post_detail(request, post_id):  # ← post_id, как в URL
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        post = get_object_or_404(
            Post,
            pk=post_id,
            is_published=True,
            pub_date__lte=now(),
            category__is_published=True
        )

    comments = post.comments.select_related('author')
    form = CommentForm()

    return render(request, 'blog/detail.html', {'post': post, 'form': form, 'comments': comments})


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    if request.user == profile_user:
        post_list = Post.objects.filter(author=profile_user)
    else:
        post_list = Post.objects.filter(
            author=profile_user,
            is_published=True,
            pub_date__lte=now()
        )
    post_list = annotate_comment_count(post_list)
    page_obj = paginate(request, post_list)

    return render(request, 'blog/profile.html', {'profile': profile_user, 'page_obj': page_obj})


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect('blog:profile', username=username)

    form = UserEditForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=username)

    return render(request, 'blog/user.html', {'form': form})


@login_required
def add_comment(request, post_id):  # ← post_id
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('blog:post_detail', post_id=post_id)


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'  # ← имя параметра из URL

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'  # ← имя параметра из URL

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop('form', None)
        return context

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop('form', None)
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})