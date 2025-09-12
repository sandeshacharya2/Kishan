from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Product, ChatRoom, Message
from accounts.models import FarmerProfile, CustomerProfile  # ← Import these!


@login_required
def farmer_dashboard(request):
    try:
        farmer_profile = request.user.farmerprofile  # Direct relation from User → FarmerProfile
    except FarmerProfile.DoesNotExist:
        return redirect('login')  # Redirect if user is not a farmer

    pending_chats = ChatRoom.objects.filter(
        farmer=farmer_profile,
        farmer_accepted=False,
        farmer_rejected=False
    )

    products = Product.objects.filter(farmer=farmer_profile)

    context = {
        'products': products,
        'pending_chats': pending_chats
    }
    return render(request, 'accounts/farmer_dashboard.html', context)


@login_required
def start_chat(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    farmer_profile = product.farmer  # Correct: Product.farmer → FarmerProfile

    # Get customer profile from current user
    try:
        customer_profile = request.user.customerprofile
    except CustomerProfile.DoesNotExist:
        return HttpResponseForbidden("You must be a registered customer to start a chat.")

    # Create or get existing chatroom (unique_together prevents duplicates)
    chatroom, created = ChatRoom.objects.get_or_create(
        product=product,
        farmer=farmer_profile,
        customer=customer_profile
    )

    if created:
        # Use sub_category instead of name (since Product has no 'name' field)
        Message.objects.create(
            chatroom=chatroom,
            sender=request.user,
            text=f"Hi {farmer_profile.user.username}, I'm interested in your product '{product.sub_category}'. Please accept this chat to continue."
        )

    return redirect('chat:chatroom_detail', chatroom_id=chatroom.id)


@login_required
def chatroom_detail(request, chatroom_id):
    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

    # Permission check: Only farmer or customer can view
    if request.user != chatroom.farmer.user and request.user != chatroom.customer.user:
        return HttpResponseForbidden("You don't have permission to view this chat.")

    # Handle rejection
    if chatroom.farmer_rejected:
        if request.user == chatroom.customer.user:
            return render(request, 'chat/chat_rejected.html', {'chatroom': chatroom})
        # Farmer can still view

    # If chat not accepted yet
    if not chatroom.farmer_accepted:
        is_farmer = request.user == chatroom.farmer.user
        messages = chatroom.message_set.all().order_by('timestamp')
        return render(request, 'chat/chatroom_pending.html', {
            'chatroom': chatroom,
            'messages': messages,
            'is_farmer': is_farmer
        })

    # Chat accepted — allow messaging
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(
                chatroom=chatroom,
                sender=request.user,
                text=text
            )
        return redirect('chat:chatroom_detail', chatroom_id=chatroom.id)

    messages = chatroom.message_set.all().order_by('timestamp')
    return render(request, 'chat/chatroom.html', {
        'chatroom': chatroom,
        'messages': messages
    })


@login_required
def accept_chat(request, chatroom_id):
    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

    if request.user != chatroom.farmer.user:
        return HttpResponseForbidden("Only the farmer can accept this chat.")

    chatroom.farmer_accepted = True
    chatroom.farmer_rejected = False
    chatroom.save()

    # Optional: Send auto message
    Message.objects.create(
        chatroom=chatroom,
        sender=chatroom.farmer.user,
        text="I've accepted your chat request. How can I help you?"
    )

    return redirect('chat:chatroom_detail', chatroom_id=chatroom.id)


@login_required
def reject_chat(request, chatroom_id):
    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

    if request.user != chatroom.farmer.user:
        return HttpResponseForbidden("Only the farmer can reject this chat.")

    chatroom.farmer_accepted = False
    chatroom.farmer_rejected = True
    chatroom.save()

    return redirect('farmer-dashboard')  # Make sure this URL name exists in your urls.py