import { Component, OnInit } from '@angular/core';
import { TeplatesService } from './templates.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-templates',
  templateUrl: './templates.component.html',
  styleUrls: ['./templates.component.scss']
})


export class TemplatesComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [];

  constructor(private service: TeplatesService){}

  ngOnInit() {
    this.collectionAction();
    this.getAllTeplates();
  }

  private getAllTeplates() {
    this.service.getAllTeplates().valueChanges.pipe(map(data => data.data.templates))
      .subscribe( (data) => {
        this.infoTemplates = data.map((item) => JSON.parse(item.info));
        console.log(this.infoTemplates);
      });
  }

  public collectionAction() {
    this.collection = [
      {
        title: 'Название',
        property: 'verbose_name'
      },
      {
        title: 'Cервер',
        property: "node",
        property_lv2: 'verbose_name'
      },
      {
        title: 'Операционная система',
        property: 'os_type'
      },
      {
        title: 'Оперативная память (MБ)',
        property: 'memory_count'
      },
      {
        title: 'Графический адаптер',
        property: 'video',
        property_lv2: 'type'
      },
      {
        title: 'Звуковой адаптер',
        property: 'sound',
        property_lv2: 'model',
        property_lv2_wrap: 'codec'
      },
      {
        title: 'Высокая доступность',
        property: 'ha_enabled'
      }
    ];
  }




}
