import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Subscription } from 'rxjs';

import { WebsocketService } from '../../../../core/services/websock.service';
import { MessengerService } from './messenger.service';


@Component({
    selector: 'tc-messenger',
    templateUrl: './messenger.component.html',
    styleUrls: ['./messenger.component.scss']
  })
export class MessengerComponent implements OnInit, OnDestroy{
  @ViewChild('messenger', { static: false }) messenger: ElementRef;
  
  private socketSub: Subscription;

  public messages: any[] = [];
  public message = new FormControl('')

  constructor(private messengerService: MessengerService, private ws: WebsocketService){}

  public ngOnInit(): void{
    this.listenSockets()
  }

  public keyEvent(e: KeyboardEvent) {
      if (e.key === 'Enter' && e.ctrlKey) {
        this.sendMessage();
      }
    }

  public sendMessage(): void {
    const message = this.message.value;
    
    this.messages.push({
      sender: 'Вы',
      self: true,
      text: message,
      time: new Date().toLocaleTimeString()
    })

    setTimeout(() => {
      this.messenger.nativeElement.scrollTop = this.messenger.nativeElement.scrollHeight
    })
    this.message.setValue('');   

    this.messengerService.sendMessageToAdmin(message).subscribe();
  }

  private listenSockets() {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/domains/').subscribe((message: any) => {
      
      if (message.msg_type === 'text_msg' ) {
        this.messages.push({
          sender: message.sender_name,
          self: false,
          text: message.message,
          time: new Date().toLocaleTimeString()
        })

        if (this.messenger) {
          setTimeout(() => {
            this.messenger.nativeElement.scrollTop = this.messenger.nativeElement.scrollHeight
          })
        }
      }         
    });
  }

  public ngOnDestroy(): void {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
