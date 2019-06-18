import { NodesService } from './../nodes.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';

@Component({
  selector: 'vdi-node-details',
  templateUrl: './node-details.component.html',
  styleUrls: ['./node-details.component.scss']
})


export class NodeDetailsComponent implements OnInit {

  public node: {} = {};
  public templates: [] = [];
  public collection = [
    {
      title: 'Название',
      property: 'verbose_name'
    },
    {
      title: 'Кластер',
      property: "cluster",
      property_lv2: "verbose_name"
    },
    {
      title: 'IP-адрес',
      property: 'management_ip'
    },
    {
      title: 'CPU',
      property: 'cpu_count'
    },
    {
      title: 'RAM',
      property: 'memory_count'
    },
    {
      title: 'Статус',
      property: 'status'
    },
    {
      title: 'Пулы данных',
      property_array: "datapools"
    },
    {
      title: 'Шаблоны ВМ',
      property_array: "templates"
    },
    {
      title: 'ВМ',
      property_array: "vms"
    }
  ];
  public collection_datapools = [
    {
      title: '№',
      property: 'index'
    },
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
  public collection_templates = [
    {
      title: '№',
      property: 'index'
    },
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
      title: 'Оперативная память (MБ)',
      property: 'memory_count'
    },
    {
      title: 'Высокая доступность',
      property_boolean: 'ha_enabled',
      property_boolean_true: 'Включена',
      property_boolean_false: 'Выключена'
    }
  ];
  public collection_vms = [
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
  public node_id:string;
  public menuActive:string = 'info';
  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    },
    {
      title: 'Cерверы',
      icon: 'server'
    }
  ];

  public spinner:boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private service: NodesService){}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.node_id = param.get('id') as string;
      this.getNode(this.node_id);
    });
  }

  private getNode(id:string) {
    this.spinner = true;
    this.service.getNode(id).valueChanges.pipe(map(data => data.data.node))
      .subscribe( (data) => {

        this.node = data;

        this.templates = data.templates.map((item) => JSON.parse(item.info));

        this.crumbs[1]['route'] = 'resourses/nodes';
        
        this.crumbs.push({
            title: `Сервер ${this.node['verbose_name']}`,
            icon: 'server'
          }
        );
      
        this.spinner = false;
      },
      (error) => {
        this.spinner = false;
      });
  }

  public routeTo(route:string): void {
    if(route === 'info') {
      this.menuActive = 'info';
    }

    if(route === 'datapools') {
      this.menuActive = 'datapools';
    }

    if(route === 'templates') {
      this.menuActive = 'templates';
    }

    if(route === 'vms') {
      this.menuActive = 'vms';
    }
  }


}
