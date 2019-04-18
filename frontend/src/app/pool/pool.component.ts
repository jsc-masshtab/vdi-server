import { Component, OnInit, Input, OnChanges } from '@angular/core';
import { PoolService } from './pool.service';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-pool-component',
  templateUrl: './pool.component.html',
  styleUrls: ['./pool.component.scss']
})


export class PoolComponent implements OnInit, OnChanges {

 @Input() rowData: object;

 public pools: object[];
 public empty: string = 'Нет доступных виртуальных машин';

public collection: object[] = [
  {
    title: '№',
    property: 'index'
  },
  {
    title: 'Название ВМ',
    property: 'verbose_name'
  },
  {
    title: 'Операционная система',
    property: 'os_type'
  },
  {
    title: 'Оперативная память(МБ)',
    property: 'memory_count'
  },
  {
    title: 'Графический адаптер',
    property: 'video',
    property_lv2: 'type'
  },
  {
    title: 'Звуковой адаптер',
    property: 'sound'
  }
]

  constructor(private service: PoolService){}

  ngOnInit() {
  
  }

  ngOnChanges() {
    if(this.rowData) {
      this.getPool();
    }
  }

  private getPool() {
    this.service.getPool(this.rowData['id']).valueChanges.pipe(map(data => data.data.pool.state.available))
      .subscribe( (data) => {
        this.pools = data.map(item => JSON.parse(item.info));
        console.log(data);
      });
  }


 // .pipe(map(data => data.data.templates))

}
