import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit } from '@angular/core';
import { DatapoolsService } from './datapools.service';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent implements OnInit {

  public datapools: object[] = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'folder-open'
    },
    {
      title: 'Тип',
      property: 'type',
      type: 'string'
    },
    {
      title: 'Диски',
      property: 'vdisk_count',
      type: 'string'
    },
    {
      title: 'Образы',
      property: 'iso_count',
      type: 'string'
    },
    {
      title: 'Файлы',
      property: 'file_count',
      type: 'string'
    },
    {
      title: 'Свободно (Мб)',
      property: 'free_space',
      type: 'string'
    },
    {
      title: 'Занято (Мб)',
      property: 'used_space',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];

  constructor(private service: DatapoolsService,private waitService: WaitService){}

  ngOnInit() {
    this.getDatapools();
  }

  public getDatapools() {
    this.waitService.setWait(true);
    this.service.getAllDatapools().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe( (data) => {
        let arrDatapools: [][] = [];
        this.datapools = [];
        arrDatapools = data.map(controller => controller.datapools);

        arrDatapools.forEach((arr: []) => {
            arr.forEach((obj: {}) => {
              this.datapools.push(obj);
            });
        });
        this.waitService.setWait(false);
      });
  }

}
