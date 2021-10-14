import { Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';


@Component({
    selector: 'app-messenger',
    templateUrl: './messenger.component.html',
    styleUrls: ['./messenger.component.scss']
  })
export class MessengerComponent{
    @ViewChild('messenger', { static: false }) messenger: ElementRef;
    
    @Input() 
      messages: any[] = [];

    @Output()
      public readonly clickSend = new EventEmitter<string>();

    message = new FormControl('')

    public keyEvent(e: KeyboardEvent) {
        if (e.key === 'Enter' && e.ctrlKey) {
          this.onClickSend();
        }
      }

    public onClickSend(): void {

      this.clickSend.emit(this.message.value)
      this.message.setValue('');   
    
        // setTimeout(() => {
        //   this.messenger.nativeElement.scrollTop = this.messenger.nativeElement.scrollHeight
        // })
        
        // this.service.sendMessageToThinClient(this.entity.user_id, message).subscribe()
      }
}
