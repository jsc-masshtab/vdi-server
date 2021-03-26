import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { DatapoolsComponent } from './datapools.component';
import { DatapoolsService } from './datapools.service';
import { of } from 'rxjs';

describe('DatapoolsComponent', () => {
  let component: DatapoolsComponent;
  let fixture: ComponentFixture<DatapoolsComponent>;

  let serviceStub: Partial<DatapoolsService>;

  beforeEach(async(() => {
    serviceStub = {
      getAllDatapools(): any {
        return {
          valueChanges: of({
            data: {
              datapools: []
            }
          })
        };
      },
      paramsForGetDatapools: {
        spin: false
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ DatapoolsComponent ],
      providers: [
        {
          provide: DatapoolsService,
          useValue: serviceStub
        }
      ],
      schemas: [
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DatapoolsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
