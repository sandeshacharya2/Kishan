from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Product, ChatRoom, Message

@login_required
def farmer_dashboard(request):
    if not request.user.is_authenticated or not request.user.profile.role == 'farmer':
        return redirect('login')

    pending_chats = ChatRoom.objects.filter(
        farmer=request.user,
        farmer_accepted=False,
        farmer_rejected=False
    )

    products = Product.objects.filter(farmer=request.user)  # if you're showing product list too

    context = {
        'products': products,
        'pending_chats': pending_chats
    }
    return render(request, 'accounts/farmer_dashboard.html', context)

@login_required
def start_chat(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    farmer = product.farmer
    customer = request.user

    print(f"[DEBUG] start_chat called: product_id={product_id}, farmer={farmer.username}, customer={customer.username}")

    # Check if chatroom exists for this product, farmer, customer
    chatroom_qs = ChatRoom.objects.filter(product=product, farmer=farmer, customer=customer)
    if chatroom_qs.exists():
        chatroom = chatroom_qs.first()
        print(f"[DEBUG] Found existing chatroom with ID {chatroom.id}")

        if chatroom.farmer_rejected:
            print("[DEBUG] Chatroom was previously rejected by farmer, resetting flags")
            chatroom.farmer_rejected = False
            chatroom.farmer_accepted = False
            chatroom.save()
    else:
        chatroom = ChatRoom.objects.create(product=product, farmer=farmer, customer=customer)
        print(f"[DEBUG] Created new chatroom with ID {chatroom.id}")

    # Create initial message if none exists
    if chatroom.message_set.count() == 0:
        Message.objects.create(
            chatroom=chatroom,
            sender=customer,
            text=f"{customer.username} wants to start a chat with you. Please accept to continue.",
        )
        print("[DEBUG] Created initial message in chatroom")

    return redirect('chat:chatroom_detail', chatroom_id=chatroom.id)


@login_required
def chatroom_detail(request, chatroom_id):
    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)
    messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')

    print(f"[DEBUG] chatroom_detail called for chatroom ID {chatroom_id}")
    print(f"[DEBUG] Farmer accepted: {chatroom.farmer_accepted}, Farmer rejected: {chatroom.farmer_rejected}")
    print(f"[DEBUG] Request user: {request.user.username}")

    # Handle farmer rejected case
    if chatroom.farmer_rejected:
        if request.user == chatroom.customer:
            print("[DEBUG] Farmer rejected chatroom - showing rejection to customer")
            return render(request, 'chat/chat_rejected.html', {'chatroom': chatroom})
        elif request.user == chatroom.farmer:
            print("[DEBUG] Farmer viewing rejected chatroom")
            # Farmer may still view chatroom
            pass
        else:
            print("[DEBUG] Unauthorized user tried to access rejected chatroom")
            return HttpResponseForbidden("You don't have permission to view this chat.")

    # If farmer hasn't accepted yet, restrict messaging
    if not chatroom.farmer_accepted:
        if request.user == chatroom.farmer:
            print("[DEBUG] Farmer sees accept/reject buttons (chat pending)")
            return render(request, 'chat/chatroom_pending.html', {
                'chatroom': chatroom,
                'messages': messages,
                'is_farmer': True
            })
        elif request.user == chatroom.customer:
            print("[DEBUG] Customer waiting for farmer acceptance")
            return render(request, 'chat/chatroom_pending.html', {
                'chatroom': chatroom,
                'messages': messages,
                'is_farmer': False
            })
        else:
            print("[DEBUG] Unauthorized user tried to access pending chatroom")
            return HttpResponseForbidden("You don't have permission to view this chat.")

    # Farmer accepted - allow messaging
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        is_bid = request.POST.get('is_bid') == 'on'
        bid_amount = request.POST.get('bid_amount') if is_bid else None
        bid_quantity = request.POST.get('bid_quantity') if is_bid else None

        print(f"[DEBUG] New message POST - text: {text}, is_bid: {is_bid}, bid_amount: {bid_amount}, bid_quantity: {bid_quantity}")

        Message.objects.create(
            chatroom=chatroom,
            sender=request.user,
            text=text,
            is_bid=is_bid,
            bid_amount=bid_amount if bid_amount else None,
            bid_quantity=bid_quantity if bid_quantity else None,
            bid_status='pending' if is_bid else None
        )

        # Refresh messages after POST
        messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')

    return render(request, 'chat/chatroom.html', {
        'chatroom': chatroom,
        'messages': messages
    })


@login_required
def accept_chat(request, chatroom_id):
    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

    print(f"[DEBUG] accept_chat called by user {request.user.username} for chatroom ID {chatroom_id}")

    if request.user != chatroom.farmer:
        print("[DEBUG] Unauthorized accept attempt")
        return HttpResponseForbidden("Only the farmer can accept this chat.")

    chatroom.farmer_accepted = True
    chatroom.farmer_rejected = False
    chatroom.save()

    print("[DEBUG] Chatroom accepted")

    return redirect('chat:chatroom_detail', chatroom_id=chatroom.id)


@login_required
def reject_chat(request, chatroom_id):
    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

    print(f"[DEBUG] reject_chat called by user {request.user.username} for chatroom ID {chatroom_id}")

    if request.user != chatroom.farmer:
        print("[DEBUG] Unauthorized reject attempt")
        return HttpResponseForbidden("Only the farmer can reject this chat.")

    chatroom.farmer_accepted = False
    chatroom.farmer_rejected = True
    chatroom.save()

    print("[DEBUG] Chatroom rejected")

    return redirect('farmer-dashboard')  # Adjust URL name if needed


@login_required
def accept_bid(request, message_id):
    message = get_object_or_404(Message, id=message_id, is_bid=True)

    print(f"[DEBUG] accept_bid called by user {request.user.username} for message ID {message_id}")

    if request.user != message.chatroom.farmer:
        print("[DEBUG] Unauthorized bid accept attempt")
        return HttpResponseForbidden("You are not allowed to accept this bid.")

    message.bid_status = 'accepted'
    message.save()

    product = message.chatroom.product
    print(f"[DEBUG] Current product stock: {product.stock_quantity}, bid quantity: {message.bid_quantity}")

    if message.bid_quantity and message.bid_quantity <= product.stock_quantity:
        product.stock_quantity -= message.bid_quantity
        product.save()
        print(f"[DEBUG] Product stock updated to {product.stock_quantity}")
    else:
        print("[DEBUG] Insufficient stock for bid quantity or no bid quantity provided")

    return redirect('chat:chatroom_detail', chatroom_id=message.chatroom.id)
