import { ErrorsService } from './errors.service';
import { Component } from '@angular/core';
import { Subscription } from 'rxjs';


@Component({
  selector: 'vdi-errors',
  templateUrl: './errors.component.html',
  styleUrls: ['./errors.component.scss']
})
export class ErrorsComponent  {

  public errors = [];
  private timers: any[] = [];
  private errorsSub:Subscription;

  constructor(private service: ErrorsService) {}

  ngOnInit() {
    this.errorsSub = this.service.getErrors().subscribe((errors: object[]) => {
      errors.forEach((item: {}) => {
        this.errors.push(item);
        this.hideMessage();
      });
    });
  }

  private hideMessage() {
    let timeFunc = setTimeout(() => {
      if(this.errors.length) {
        //console.log(valueRemove,'remove');
        this.errors.splice(0,1);
        //this.timers.splice(0,1);
        // setTimeout(() => {
        //   this.errors.splice(0,valueRemove);
        //   console.log(valueRemove,'remove');
        // },8000); 
      } else {
        console.log('return')
      }
      
      return; 
    },8000);
    this.timers.push(timeFunc);
    console.log(this.timers,'this.timers');
  }

  public closeMessage(id) {
    this.errors.splice(id, 1);
    clearTimeout(this.timers[id]);
    this.timers.splice(id,1);
  }

  ngOnDestroy() {
    this.errorsSub.unsubscribe();
  }

}
