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
      class: 'name-start'
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

  public spinner:boolean = false;

  constructor(private service: DatapoolsService){}

  ngOnInit() {
    this.getDatapools();
  }

  public getDatapools() {
    this.spinner = true;
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
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

}
