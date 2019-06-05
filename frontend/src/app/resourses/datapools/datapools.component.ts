import { Component, OnInit } from '@angular/core';
import { DatapoolsService } from './datapools.service';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent implements OnInit {

  public datapools: {};
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name'
    },
    {
      title: 'Тип',
      property: "type"
    },
    {
      title: 'Диски',
      property: 'vdisk_count'
    },
    {
      title: 'Образы',
      property: 'iso_count'
    },
    {
      title: 'Файлы',
      property: 'file_count'
    },
    {
      title: 'Свободно (Мб)',
      property: 'free_space'
    },
    {
      title: 'Занято (Мб)',
      property: 'used_space'
    },
    {
      title: 'Статус',
      property: 'status'
    }
  ];

  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    }
  ];

  public spinner:boolean = true;

  constructor(private service: DatapoolsService){}

  ngOnInit() {
    this.getDatapools();
  }

  private getDatapools() {
    this.service.getAllDatapools().valueChanges.pipe(map(data => data.data.datapools))
      .subscribe( (data) => {
        this.datapools = data;
        this.crumbs.push({
          title: `Пулы данных`,
          icon: 'folder-open'
        });
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

}
