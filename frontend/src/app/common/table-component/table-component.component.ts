import { Subscription } from 'rxjs';
import { Component,Input, Output, EventEmitter, OnDestroy, OnInit } from '@angular/core';
import { TableService } from './table-component.service';


@Component({
  selector: 'vdi-table-component',
  templateUrl: './table-component.component.html',
  styleUrls: ['./table-component.component.scss']
})
export class TableComponentComponent implements OnInit,OnDestroy {


  @Input() data: object[] = [];
  @Input() spinner:boolean = false;
  @Input() collection: object[] = [];
  @Input() cursor: boolean = false;
  @Input() empty: string = "- нет данных -";
  @Output() clickRowData:EventEmitter<any> = new EventEmitter();
  private spinSub:Subscription;

  constructor(private service: TableService) {}

  ngOnInit() {
   this.spinSub =  this.service.getStateSpinner().subscribe((spin: boolean) => {
     this.spinner = spin;
      console.log(spin);
    });
  }

  public clickRow(item) {
    this.clickRowData.emit(item);
  }

  ngOnDestroy() {
    this.spinSub.unsubscribe();
  }

  
}
