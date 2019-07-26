import { Component, OnInit } from '@angular/core';
import { VmsService } from './vms.service';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-vms',
  templateUrl: './vms.component.html',
  styleUrls: ['./vms.component.scss']
})


export class VmsComponent implements OnInit {

  public vms: object[] = [];
  public collection = [
    {
      title: 'Название',
      property: 'name',
      class: 'name-start'
    },
    {
      title: 'Сервер',
      property: "node",
      property_lv2: 'verbose_name'
    },
    {
      title: 'Шаблон',
      property: "template",
      property_lv2: 'name'
    },
    {
      title: 'Статус',
      property: "state"
    }
  ];


  public spinner:boolean = false;

  constructor(private service: VmsService){}

  ngOnInit() {
    this.getAllVms();
  }

  private getAllVms() {
    this.spinner = true;
    this.service.getAllVms().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data)=> {
    
      let arrVms: [][] = [];
      this.vms = [];
      arrVms = data.map(controller => controller.vms);

      arrVms.forEach((arr: []) => {
          arr.forEach((obj: {}) => {
            this.vms.push(obj);
          }); 
      });
      this.spinner = false;
    },(error) => {
      this.spinner = false;
    });
  }
}
