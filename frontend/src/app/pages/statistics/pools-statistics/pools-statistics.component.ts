import { Component, OnInit } from '@angular/core';
import { AbstractControl, FormBuilder, FormControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { ApolloQueryResult } from '@apollo/client/core';
import { WaitService } from '@app/core/components/wait/wait.service';
import { PoolStatisticsCollections } from './collections';

import { PoolStatisticsService, QueryParams } from './pool-statistics.service';

function startMonthValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {

    const value = control.value;

    if (!value) {
      return null;
    }

    const startDateLimit = new Date(new Date().getTime() - (90 * 24 * 60 * 60 * 1000));       // 3 months ago

    return value.getTime() < startDateLimit ? { startDate: true } : null;
  };
}

@Component({
  selector: 'vdi-pools-statistics',
  templateUrl: './pools-statistics.component.html',
  styleUrls: ['./pools-statistics.component.scss']
})
export class PoolsStatisticsComponent extends PoolStatisticsCollections implements OnInit {

  used_pools_overall: any[];
  used_client_os: any[];
  used_client_versions: any[];
  users: any[];

  conn_number_by_time_interval: any[];

  constructor(
    private poolStatService: PoolStatisticsService, 
    private formBuilder: FormBuilder,
    private waitService: WaitService,
  ) {
    super();
  }

  colors = ["#acd2ee", "#e3cff7", "#f8bfa3", "#cdd2c1", "#8eced4", "#c9aacd", "#cbd4aa", "#db87ba", "#8ae487", "#c59eaf", "#a3dab1", "#f58cbb", "#ebddd3", "#91d295", "#eab2f9", "#fa81c1", "#c1faa8", "#ebc7a5", "#9ab097", "#cdf5eb"]

  public pool: FormControl = new FormControl('all');
  public period: FormControl = new FormControl(1);
  public range =  this.formBuilder.group({
    start: [, [startMonthValidator()]],
    end: [] 
  });

  public pools = [];
  public statistics: any = {};
 
  ngOnInit() {
    this.refresh();

    this.range.valueChanges.subscribe((value) => {
      if(value.start && value.end && this.range.valid) {
        this.period.setValue(0);
        this.getStatistics();
      }
    });

    this.period.valueChanges.subscribe((value) => {
      if(value) {
        this.range.reset();
        this.getStatistics();
      }
    });

    this.pool.valueChanges.subscribe(() => {
      this.getStatistics();
    })
  }

  public refresh(): void {
    this.getAllPools();
    this.getStatistics();
  }

  public getAllPools(): void {
    this.poolStatService.getAllPools().valueChanges.subscribe((res: ApolloQueryResult<any>) => {      
      this.pools = res.data.pools;
    })
  }

  public getStatistics() {
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (this.period.value * 24 * 60 * 60 * 1000));
    
    let params: QueryParams = { 
      startDate, endDate
    }
    
    if (this.pool.value !== 'all') {
      params.poolId = this.pool.value;
    }

    if (this.range.value.start && this.range.value.end) {  
      params = { 
        startDate: this.range.value.start, 
        endDate: this.range.value.end 
      }
    }

    this.waitService.setWait(true);
    this.poolStatService.getPoolStatistics(params).valueChanges.subscribe((res: ApolloQueryResult<any>) => {

      this.statistics = res.data.pool_usage_statistics;

      this.used_pools_overall = this.barCalculate('used_pools_overall');
      this.used_client_os = this.barCalculate('used_client_os');
      this.used_client_versions = this.barCalculate('used_client_versions');
      this.users = this.barCalculate('users');

      this.conn_number_by_time_interval = this.barCalculate('conn_number_by_time_interval', 'time_interval');

      console.log(this.statistics)

      this.waitService.setWait(false);
    });
  }

  barCalculate(property, name: string ='name', value: string ='conn_number') {
    return this.statistics[property].map((el, index) => {

      let summValue = [...this.statistics[property].map(stat => stat[value])].reduce((a, b) => a + b, 0);

      return {
        ...el,
        name: el[name],
        color: index < this.colors.length ? this.colors[index] : this.generateLightColorHex(),
        value: el[value] ? Math.round(el[value] / summValue * 100) : 0
      }
    });
  }

  generateLightColorHex() {
    let color = "#";
    for (let i = 0; i < 3; i++) {
      color += ("0" + Math.floor(((1 + Math.random()) * Math.pow(16, 2)) / 2).toString(16)).slice(-2);
    }
    return color;
  }
}
