from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST


def post_list(request):
    post_list = Post.published.all()
    # Постраничная разбивка
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)  # Если номер страницы не int, то возвращает первую страницу
    except EmptyPage:
        # Если будет отсутствовать номер страницы в диапазоне, то вернется последняя существующая страница
        posts = paginator.page(paginator.num_pages)  # num-pages выдает общее кол-во страниц,
        # поэтому число совпадает с номером последней страницы
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    comments = post.comments.filter(active=True)  # Список активных комментариев
    form = CommentForm()  # Форма для комментирования пользователем
    return render(request, 'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'form': form})


def post_share(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)

    sent = False

    if request.method == 'POST':
        # Форма передана в обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = f"{cd['name']} recommends you read" \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'your_account@gmail.ru', [cd['to']])
            sent = True
            # отправить электронное письмо
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)  # Комментарий был отправлен
    if form.is_valid():
        comment = form.save(commit=False)  # Создается объект класса, не сохраняя его в БД
        comment.post = post  # Назначается пост комментарию
        comment.save()
    return render(request, 'blog/post/comment.html', {'post': post,
                                                      'form': form,
                                                      'comment': comment})

