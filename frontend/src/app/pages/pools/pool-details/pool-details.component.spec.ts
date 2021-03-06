import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { PoolDetailsComponent } from './pool-details.component';
import { PoolDetailsService } from './pool-details.service';

describe('PoolDetailsComponent', () => {
  let component: PoolDetailsComponent;
  let fixture: ComponentFixture<PoolDetailsComponent>;

  let dialogStub: Partial<MatDialog>;
  let poolServiceStub: Partial<PoolDetailsService>;

  beforeEach(waitForAsync(() => {
    poolServiceStub = {
      getPool(): any {
        return {
          valueChanges: of({
            data: {
              pool: {}
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ PoolDetailsComponent ],
      providers: [
        {
          provide: PoolDetailsService,
          useValue: poolServiceStub
        },
        {
          provide: MatDialog,
          useValue: dialogStub
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PoolDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
