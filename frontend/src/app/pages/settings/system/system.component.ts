import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { ApolloQueryResult } from '@apollo/client/core';

import { DetailsMove } from '@shared/classes/details-move';
import { Subscription } from 'rxjs';
import { INetwork, ISystemData, ISystemResponse, SystemMapper } from './system.mapper';
import { SystemService } from './system.service';

@Component({
  selector: 'vdi-system',
  templateUrl: './system.component.html',
  styleUrls: ['./system.component.scss']
})


export class SystemComponent extends DetailsMove implements OnInit {

  private sub: Subscription;

  public tabs: string[] = ['Время', 'Интерфейсы'];
  public activeTab: string = this.tabs[0];
  public networksList: INetwork[] = [];
  public dateInfo: Pick<ISystemData, 'timezone' | 'localTime'>;

  @ViewChild('view', { static: true }) view: ElementRef;
  
  public readonly intoCollection: ReadonlyArray<object> = [
    {
      title: 'Часовой пояс',
      property: 'timezone',
      type: 'string'
    },
    {
      title: 'Время',
      property: 'localTime',
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

  public onResize(): void {
    super.onResize(this.view);
  }

  public ngOnInit(): void {
    this.getSystemInfo();
  }

  public changeTab(tab: string): void{
      this.activeTab = tab;
  }

  public getSystemInfo(): void {

    if (this.sub) {
      this.sub.unsubscribe();  
    }

    this.sub = this.systemService.getSystemInfo().valueChanges.subscribe((res: ApolloQueryResult<ISystemResponse>) => {

      const mapper = new SystemMapper();
      const result = mapper.serverModelToClientModel(res.data.system_info);      

      this.dateInfo = {
        timezone: result.timezone,
        localTime: result.localTime
      };

      this.networksList = result.networksList.map((item: INetwork) => ({ name: item.name, ip: item.ip }));
      
      this.sub.unsubscribe();
    });
  }
}






