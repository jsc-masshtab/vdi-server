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
      title: '№',
      property: 'index'
    },
    {
      title: 'Название',
      property: 'name'
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
    }
  ];

  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    },
    {
      title: `Виртуальные машины`,
      icon: 'desktop'
    }
  ];

  public spinner:boolean = false;

  constructor(private service: VmsService){}

  ngOnInit() {
    this.getAllVms();
  }

  private getAllVms() {
    this.spinner = true;
    this.service.getAllVms().valueChanges.pipe(map(data => data.data.vms)).subscribe((res)=> {
      this.vms = res;
      this.spinner = false;
    },(error) => {
      this.spinner = false;
    });
  }
}
