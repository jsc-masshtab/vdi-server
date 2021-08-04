import { Component, OnInit } from '@angular/core';

import { DetailsMove } from '@shared/classes/details-move';
import { SystemService } from './system.service';

@Component({
  selector: 'vdi-system',
  templateUrl: './system.component.html',
  styleUrls: ['./system.component.scss']
})


export class SystemComponent extends DetailsMove implements OnInit {

  public networksList: any = [];
  public dateInfo = {};
  public readonly intoCollection: ReadonlyArray<object> = [
    {
      title: 'Часовой пояс',
      property: 'timezone',
      type: 'string'
    },
    {
      title: 'Время',
      property: 'date',
      type: 'time'
    },
  ]
  public readonly tableCollection: ReadonlyArray<object> = [
   {
      title: 'Название',
      property: 'name',
      type: 'string'
    },
    {
      title: 'ipv4',
      property: 'ip',
      type: 'string'
    },
  ];

  constructor(private systemService: SystemService){
    super()
  }

  ngOnInit() {
   this.systemService.getSystemInfo().valueChanges.subscribe((res) => {
      const result = res.data.system_info;  
      this.dateInfo = {timezone: result.time_zone, date: result.local_time};
      this.networksList = res.data.system_info.networks_list.map(item => ({ name:item.name, ip: item.ipv4}));
    });
  }

}
