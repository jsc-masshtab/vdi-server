import { Component, OnInit } from '@angular/core';
import { VmsService } from './vms.service';
import { map } from 'rxjs/operators';
import { WaitService } from '../../../common/components/wait/wait.service';

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


  constructor(private service: VmsService, private waitService: WaitService){}

  ngOnInit() {
    this.getAllVms();
  }

  public getAllVms() {
    this.waitService.setWait(true);
    this.service.getAllVms().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data)=> {
    
      let arrVms: [][] = [];
      this.vms = [];
      arrVms = data.map(controller => controller.vms);

      arrVms.forEach((arr: []) => {
          arr.forEach((obj: {}) => {
            this.vms.push(obj);
          }); 
      });
      this.waitService.setWait(false);
    });
  }
}
