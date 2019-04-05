import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { PoolsService } from './polls.service';

@Component({
  selector: 'vdi-polls',
  templateUrl: './polls.component.html',
  styleUrls: ['./polls.component.scss']
})
export class PollsComponent implements OnInit {

  public pools: [];

  public collection: object[] = [
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Размер (ГБ)',
      property: 'initial_size'
    },
    {
      title: 'Состояние',
      property: 'state',
      property_lv2: 'running'
    },
    {
      title: 'Занятые ВМ',
      property: 'initial_size'
    },
    {
      title: 'Свободные ВМ',
      property: 'reserve_size'
    }
  ];

  public crumbs: object[] = [
    {
      title: 'Пулы виртуальных машин',
      icon: 'desktop'
    }
  ];

  constructor(private service: PoolsService){}

  ngOnInit() {
    this.getAllPools();
  }

  private getAllPools() {
    this.service.getAllPools().valueChanges.pipe(map(data => data.data.pools))
      .subscribe( (data) => {
        this.pools = data;
         console.log(this.pools);
      });
  }

}
